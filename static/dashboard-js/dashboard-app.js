import React, { Component } from 'react';

class App extends Component {
  constructor(props) {
    super(props);
    this.state = {
      campaignsList: [],
      canCreate: true,
    };
  }

  componentDidMount() {
    fetch('http://localhost:5000/api/games/')
      .then(response => response.json())
      .then(campaignsList => this.setState({ campaignsList }));
  }

  render() {
    return (
      <React.Fragment>
        {this.state.campaignsList.map(campaign => <div key={campaign.id}>{campaign.name}</div>)}
        <div>
          <input type="text" placeholder="Campaign name"></input>
          <button onClick={() => this.createNewCampaign('Bingo')}>Create new campaign</button>
          <p hidden={this.state.canCreate}>You cannot.</p>
          <button onClick={this.logout}>Sign out</button>
        </div>
      </React.Fragment>
    );
  }

  createNewCampaign = name => {
    fetch('http://localhost:5000/api/games/', {
      method: 'POST',
      body: JSON.stringify({'name': name}),
      headers: {
        'Content-Type': 'application/json'
      }
    })
      .then(response => response.json())
      .then(campaignsList => this.setState({ campaignsList }))
  }

  logout = () => {
    window.location.replace("http://localhost:5000/logout/");
  }
}

export default App;