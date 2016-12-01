import React from "react";
import ReactDOM from "react-dom";
import polyfill from "es6-promise";
import "isomorphic-fetch";

/* ********
 * fetch() helper functions for Promise then-chain processing
 * ********
 */

function fetchStatus(response) {  
    if (response.status >= 200 && response.status < 300) {  
        return Promise.resolve(response)  
    } else {  
        return Promise.reject(new Error(response.statusText))  
    }  
}

function fetchJSON(response) {  
    return response.json()  
}

function fetchGenError(error) {
    console.log('Request failed', error);
}

/* ********
 * React components
 * ********
 */

var Dashboard = React.createClass({
    render: function() {
        return <div>You are logged in and have reached the dashboard.</div>;
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
        .then(fetchStatus)
        .then(fetchJSON)
        .then(function(json) {
            // DEBUG
            console.log('Response message: ' + json['message']);
            console.log('Error message: ' + json['error']);
            // DEBUG
            // TODO: Incorporate message/error text into user feedback.
            if (json['logged_in']) {
                that.props.setLogin(true);
            }
        }).catch(fetchGenError);
    },

    render: function() {
        return (
            <div className="login">
                <h2>Login</h2>
                <form className="form-horizontal">
                    <div className="form-group">
                        <label for="inputUsername" className="col-sm-2 control-label">Username</label>
                        <div className="col-sm-3">
                            <input type="text" className="form-control" id="inputUsername" placeholder="Username" />
                        </div>
                    </div>
                    <div className="form-group">
                        <label for="inputPassword" className="col-sm-2 control-label">Password</label>
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

var Nido = React.createClass({
    getInitialState: function() {
        return {
            loginState: false
        };
    },

    setLoginState: function(state) {
        this.setState({
            loginState: state
        });
    },
    
    render: function() {
        if (this.state.loginState) {
            return <Dashboard setLogin={this.setLoginState} />;
        } else {
            return <LoginForm setLogin={this.setLoginState} />;
        }
    }
});

// Render and pass Flask login state to Nido component
ReactDOM.render(
  <Nido />,
  document.getElementById('nido')
);
