import React from "react";
import ReactDOM from "react-dom";
import polyfill from "es6-promise";
import "isomorphic-fetch";

/* ********
 * fetch() helper functions for Promise then-chain processing
 * ********
 */

function fetchCheckStatus(response) {  
    if (response.status >= 200 && response.status < 300) {  
        return Promise.resolve(response)
    } else {  
        return Promise.reject(new Error(response.statusText))
    }  
}

function fetchResponseJSON(response) {  
    return response.json()
}

function fetchGenericError(error) {
    console.log('Request failed: ', error);
}

/* ********
 * fetch() calls
 * ********
 */

function fetchData(updateFunc, route, key) {
    fetch('/' + route, {
        method: 'POST',
        credentials: 'include'
    })
    .then(fetchCheckStatus)
    .then(fetchResponseJSON)
    .then(function(json) {
        if (json) {
            updateFunc(json, key);
        } else {
            return Promise.reject(new Error('No JSON in reponse body.'))
        }
    }).catch(fetchGenericError);
    
    return
}

/* ********
 * React components
 * ********
 */

var Dashboard = React.createClass({
    getInitialState: function() {
        return {
            config: undefined,
            state: undefined,
            weather: undefined,
            user: this.props.userInfo
        };
    },

    updateDashboardState: function(data, key) {
        if ( key in data ) {
            this.setState({
                [key]: data[key]
            });
        } else if ( 'error' in data ) {
            this.setState({
                [key]: data
            });
        } else {
            throw('Unexpected error retrieving ' + key + ' data. Server returned: ' + data);
        }
    },

    componentDidMount: function() {
        // This component only loads if the user is logged in
        // Make calls to get_config, get_state, get_weather and get_user (if necessary)
        fetchData(this.updateDashboardState, 'get_config', 'config');
        fetchData(this.updateDashboardState, 'get_state', 'state');
        fetchData(this.updateDashboardState, 'get_weather', 'weather');
        if ( this.state.user == undefined ) {
            fetchData(this.updateDashboardState, 'get_user', 'user');
        }
    },

    render: function() {
        return(
                <div>
                <p><strong>Config:</strong></p>
                <p>{JSON.stringify(this.state.config)}</p>
                <p><strong>State:</strong></p>
                <p>{JSON.stringify(this.state.state)}</p>
                <p><strong>Weather:</strong></p>
                <p>{JSON.stringify(this.state.weather)}</p>
                <p><strong>User:</strong></p>
                <p>{JSON.stringify(this.state.user)}</p>
                </div>
              );
    }
});

var LoginForm = React.createClass({
    onLoginSubmit: function() {
        // Set up username/password form data
        var form = new FormData();
        form.append("username", document.getElementById('inputUsername').value);
        form.append("password", document.getElementById('inputPassword').value);
       
        // Preserve scope 
        var that = this;
        // Make the login request, AJAX-style with fetch()
        fetch('/login', {
            method: 'POST',
            body: form,
            credentials: 'include'
        })
        .then(fetchCheckStatus)
        .then(fetchResponseJSON)
        .then(function(json) {
            // TODO: Incorporate message/error text into user feedback.
            if (json['logged_in']) {
                that.props.setLogin(true);
            }
        }).catch(fetchGenericError);
    },

    render: function() {
        return (
            <div className="login">
                <h2>Login</h2>
                <form className="form-horizontal">
                    <div className="form-group">
                        <label htmlFor="inputUsername" className="col-sm-2 control-label">Username</label>
                        <div className="col-sm-3">
                            <input type="text" className="form-control" id="inputUsername" placeholder="Username" />
                        </div>
                    </div>
                    <div className="form-group">
                        <label htmlFor="inputPassword" className="col-sm-2 control-label">Password</label>
                        <div className="col-sm-3">
                            <input type="password" className="form-control" id="inputPassword" placeholder="Password" />
                        </div>
                    </div>
                    <div className="form-group">
                        <div className="col-sm-offset-2 col-sm-2">
                            <button type="button" onClick={this.onLoginSubmit} className="btn btn-default">Sign in</button>
                        </div>
                    </div> 
                </form>
            </div>
            );
    }
});

var Loading = React.createClass({
    render: function() {
        return <div className="loading"></div>;
    }
});

var Nido = React.createClass({
    getInitialState: function() {
        return {
            loadingState: true,
            loginState: false,
            userInfo: undefined
        };
    },

    setLoginState: function(state) {
        this.setState({
            loginState: state
        });
    },

    setLoadingState: function(state) {
        this.setState({
            loadingState: state
        });
    },

    setUserInfo: function(info) {
        this.setState({
            userInfo: info
        });
    },

    componentDidMount: function() {
        // Preserve scope 
        var that = this;
        // Make a request to /get_user and check response to determine what to do next
        fetch('/get_user', {
            method: 'POST',
            credentials: 'include'
        })
        // Valid response status?
        .then(function(response) {
            if ( (response.status == 403) || (response.status >= 200 && response.status < 300) ) {
                return Promise.resolve(response)
            } else {  
                return Promise.reject(new Error(response.statusText))
            }  
        })
        // Is the user logged in?
        .then(function(response) {
            if ( response.status == 403 ) {
                that.setLoginState(false);
                that.setLoadingState(false);
            } else {
                that.setLoginState(true);
                response.json().then(function(json) {
                    if ( 'user' in json ) {
                        that.setUserInfo(json['user']);
                    }
                    that.setLoadingState(false);
                });
            }
        })
        .catch(fetchGenericError);
    },
    
    render: function() {
        if (this.state.loadingState) {
            return <Loading />;
        } else {
            if (this.state.loginState) {
                return <Dashboard setLogin={this.setLoginState} userInfo={this.state.userInfo} />;
            } else {
                return <LoginForm setLogin={this.setLoginState} />;
            }
        }
    }
});

ReactDOM.render(
  <Nido />,
  document.getElementById('nido')
);
