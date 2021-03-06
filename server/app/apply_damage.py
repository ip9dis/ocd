def apply_damage(amount, game_id, character, damage_type):
    """
    Applies the damage to the character or monster.
    Changes statuses of character/monster according to it's hit points.
    """
    new_status = None
    msg = {}
    db_update_object = {}

    msg["type"] = "apply_damage"

    # Check if target has resistance to that type of damage.
    if damage_type in character['buffs']['resistances']:
        amount /= 2
    elif 'resistances' in character['buffs']['temporary']:
        for buff in character['buffs']['temporary']['resistances']:
            if damage_type == buff['value']:
                amount /= 2

    # Check if character has temporary temporary hit points (No pun intended).
    if 'temporary_hit_points' in character['buffs']['temporary']:
        # For each temporary hit points buff.
        for buff in character['buffs']['temporary']['temporary_hit_points']:
            if buff['amount'] >= amount:
                # Temporary hit points can absorb all the damage amount.
                absorbed_amount = amount
            else:
                # All temporary hit points are spent but not all damage amount is covered.
                absorbed_amount = buff['amount']

            # Reduce the temporary hit points.
            combat_session_monsters_collection.update_one(
                {'game_id': game_id,
                 'character_documents.combat_identifier': character['combat_identifier']},
                {'$inc': {'character_documents.$.buffs.temporary.temporary_hit_points': -absorbed_amount}})

            # Reduce damage amount by absorbed amount.
            amount = amount - absorbed_amount

    # Check if character has temporary current hit points.
    if 'current_hit_points' in character['buffs']['temporary']:
        # For each current hit points buff.
        for buff in character['buffs']['temporary']['current_hit_points']:
            # Increase current hit points of the character by the buff amount.
            character['current_hit_points'] += buff['amount']

    # Calculate the character's current hit points, after substracting the damage.
    after_hit_points = character['current_hit_points'] - amount

    msg["damage_amount"] = amount

    # See if character has maximum hit points buff.
    if 'maximum_hit_points' in character['buffs']['temporary']:
        for buff in character['buffs']['temporary']['maximum_hit_points']:
            # Increase maximum hit points of the character by the buff amount.
            character['maximum_hit_points'] += buff['amount']

    # Characters can change heath status to 'unconscious', before 'dead'.
    if character['type'] == 'player_character':
        if after_hit_points <= -character['maximum_hit_points']:
            new_status = 'dead'
        elif after_hit_points <= 0:
            new_status = 'unconscious'
    elif character['type'] == 'monster':
        # Change displayed health status.
        percentage = after_hit_points / character['maximum_hit_points']
        
        if percentage <= 0:
            displayed_hp_status = 'Dead'
        elif percentage == 1:
            displayed_hp_status = 'Undamaged'
        elif percentage >= 0.75:
            displayed_hp_status = 'Minor wounded'
        elif percentage >= 0.50:
            displayed_hp_status = 'Wounded'
        elif percentage >= 0.25:
            displayed_hp_status = 'Heavily wounded'
        else:
            displayed_hp_status = 'Severely wounded'

        db_update_object['character_documents.$.displayed_hp_status'] = displayed_hp_status

        # Monsters get directly to 'dead' if they drop to zero hit points.
        if after_hit_points <= 0:
            new_status = 'dead'

            # Split monster's experience points to the characters.
            split_monster_exp(character, game_id)

    if new_status == 'dead':
        # Remove the dead player character from the initiative order list,
        # and decrease the round length by 1.
        combat_session_monsters_collection.update_one(
            {'game_id': game_id},
            {'$pull': {'initiative_order': character['combat_identifier']},
             '$inc': {'round_length': -1}})

    db_update_object['character_documents.$.current_hit_points'] = after_hit_points

    if new_status == 'dead' or new_status == 'unconscious':
        db_update_object['character_documents.$.health_status'] = new_status

    # Update the current hit points and status of the character.
    updated_characters = combat_session_monsters_collection.find_one_and_update(
        {'game_id': game_id,
         'character_documents.combat_identifier': character['combat_identifier']},
        {'$set': db_update_object}, return_document=ReturnDocument.AFTER)['character_documents']

    for updated_character in updated_characters:
        if updated_character['combat_identifier'] == character['combat_identifier']:
            msg['damaged_character'] = updated_character
            msg['damaged_character'].pop('_id', None)

    return msg