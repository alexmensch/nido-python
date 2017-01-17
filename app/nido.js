import React from "react";
import ReactDOM from "react-dom";
import polyfill from "es6-promise";
import "isomorphic-fetch";

/* ********
 * fetch() helper functions for Promise then-chain processing
 * ********
 */

function fetchCheckStatus2xx(response) {  
    if (response.status >= 200 && response.status < 300) {  
        return Promise.resolve(response)
    } else {  
        return Promise.reject(new Error(response.statusText))
    }  
}

function fetchCheckStatus2xx403(response) {  
    if (response.status == 403 || response.status >= 200 && response.status < 300) {  
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

function fetchData(route) {
    return fetch('/' + route, {
        method: 'POST',
        credentials: 'include'
    })
    .catch(fetchGenericError);
}

/* ********
 * React components
 * ********
 */

var FormButton = React.createClass({
    // Received props:
    // buttonText, clickAction (func), buttonClass, divClass
    render: function() {
        return (
            <div className="form-group">
                <div className={this.props.divClass}>
                    <button type="button" onClick={this.props.clickAction}
                            className={'btn ' + this.props.buttonClass}>{this.props.buttonText}</button>
                </div>
            </div>
            );
    }
});

var FormRow = React.createClass({
    // Received props:
    // labelClass, inputDivClass, inputType, inputPlaceholder (string or list), labelText
    render: function() {
        var input_id = this.props.inputId ? this.props.inputId : 'input-' + this.props.labelText;
        switch(this.props.inputType) {
            case 'text':
            case 'password':
                return (
                    <div className="form-group">
                        <label htmlFor={input_id} className={'control-label ' + this.props.labelClass}>{this.props.labelText}</label>
                        <div className={this.props.inputDivClass}>
                            <input type={this.props.inputType} className="form-control" id={input_id}
                                   placeholder={this.props.inputPlaceholder} />
                        </div>
                    </div>
                    );
            case 'checkbox':
            case 'radio':
                return (
                    <div className="form-group">
                        <label htmlFor={input_id} className={'control-label ' + this.props.labelClass}>{this.props.labelText}</label>
                        <div id={input_id} className={this.props.inputDivClass} >
                            {this.props.inputPlaceholder.map((item) =>
                                <div className={this.props.inputType} key={item}>
                                    <label>
                                        <input type={this.props.inputType} name={this.props.inputType + '-' + this.props.labelText}
                                            id={input_id + '-' + item} value={item} />
                                        {item}
                                    </label>
                                </div>
                            )}
                        </div>
                    </div>
                    );
            case 'select':
                return (
                    <div className="form-group">
                        <label htmlFor={input_id} className={'control-label ' + this.props.labelClass}>{this.props.labelText}</label>
                        <select className="form-control" name={this.props.inputType + '-' + this.props.labelText}
                                id={input_id} className={this.props.inputDivClass} >
                            {this.props.inputPlaceholder.map((item) =>
                               <option value={item} key={item}>{item}</option> 
                            )}
                        </select>
                    </div>
                       );
            case 'textarea':
                return (
                    <div className="form-group">
                        <label htmlFor={input_id} className={'control-label ' + this.props.labelClass}>{this.props.labelText}</label>
                        <div className={this.props.inputDivClass}>
                            <textarea className="form-control" id={input_id} rows="3">{this.props.inputPlaceholder}</textarea>
                        </div>
                    </div>
                       );
            default:
                throw('Unexpected inputType property passed to FormRow component: ' + this.props.inputType);
        }
    }
});

var FormRowsFromObject = React.createClass({
    // Received props:
    // data (object), labelClass, inputDivClass
    render: function() {
        var formRows = [];
        for (var row in this.props.data) {
            if (this.props.data.hasOwnProperty(row)) {
                formRows.push(row);
            }
        }

        return (
            <div className="configFormRows">
            {formRows.map((key) =>
                <FormRow labelClass={this.props.labelClass} inputDivClass={this.props.inputDivClass}
                         inputType={this.props.data[key].form_data[0]}
                         inputPlaceholder={this.props.data[key].form_data[1]}
                         labelText={this.props.data[key].label}
                         key={key} />
                         )}
            </div>
            );
    }
});

var Config = React.createClass({
    // Props: setView (function), config (JSON)
    onConfigSubmit: function() {
        return
    },

    render: function() {
        return (
                <div id="config">
                    <h2>Nido Configuration</h2>
                    <form className="form-horizontal">
                        <FormRowsFromObject data={this.props.config.config}
                                            labelClass="col-sm-2" inputDivClass="col-sm-3" />
                        <FormButton buttonText="Save" clickAction={this.onConfigSubmit}
                                    buttonClass="btn-default" divClass="col-sm-offset-2 col-sm-2" />
                    </form>
                </div>
               );
    }
});

var Toolbar = React.createClass({
    // Props: setView (function)
    configAction: function() {
        return
    },

    logoutAction: function() {
        return
    },

    render: function() {
        return (
                <div id="toolbar">
                    <ToolbarButton icon={undefined} action={this.configAction} />
                    <ToolbarButton icon={undefined} action={this.logoutAction} />
                </div>
                );
    }
});

var ToolbarButton = React.createClass({
    // Props: icon, action (function)
    render: function() {
        return <span>ToolbarButton</span>;
    }
});

var Dashboard = React.createClass({
    // Props: setView (function), config (JSON), state (JSON), weather (JSON)
    render: function() {
        return(
                <div>
                    <Toolbar setView={this.props.setView} />
                    <div id="dashboard">
                        <NidoState state={this.props.state} config={this.props.config} />
                        <Weather weather={this.props.weather} />
                    </div>
                </div>
              );
    }
});

var NidoState = React.createClass({
    // Props: state (JSON), config (JSON)
    render: function() {
        return(
            <div>
                <div id="nidoState">
                    <div><strong>State:</strong>{JSON.stringify(this.props.state)}</div>
                    <div><strong>Config:</strong>{JSON.stringify(this.props.config)}</div>
                </div>
                <div id="userControls">
                    <div id="changeSetpoint"><ChangeSetpoint config={this.props.config} /></div>
                    <div id="onOff"><OnOff config={this.props.config} /></div>
                </div>
            </div>
            );
    }
});

var ChangeSetpoint = React.createClass({
    // Props: config (JSON)
    render: function() {
        return <span>ChangeSetpoint</span>;
    }
});

var OnOff = React.createClass({
    // Props: config (JSON)
    render: function() {
        return <span>OnOff</span>;
    }
});

var Weather = React.createClass({
    // Props: weather (JSON)
    render: function() {
        return(
            <div id="weather">
                <div><strong>Weather:</strong>{JSON.stringify(this.props.weather)}</div>
            </div>
            );
    }
});

var Login = React.createClass({
    // Login: setView (function)
    onLoginSubmit: function() {
        // Set up username/password form data
        var form = new FormData();
        form.append("username", document.getElementById('input-Username').value);
        form.append("password", document.getElementById('input-Password').value);
       
        // Preserve scope 
        var that = this;
        // Make the login request, AJAX-style with fetch()
        fetch('/login', {
            method: 'POST',
            body: form,
            credentials: 'include'
        })
        .then(fetchCheckStatus2xx)
        .then(fetchResponseJSON)
        .then(function(json) {
            // TODO: Incorporate message/error text into user feedback.
            if (json['logged_in'] == true) {
                that.props.setView('dashboard');
            }
        }).catch(fetchGenericError);
    },

    render: function() {
        return (
            <div className="login">
                <h2>Login</h2>
                <form className="form-horizontal">
                    <FormRow labelText="Username" labelClass="col-sm-2" inputId="input-Username"
                             inputDivClass="col-sm-3" inputType="text" inputPlaceholder="Username" />
                    <FormRow labelText="Password" labelClass="col-sm-2" inputId="input-Password"
                             inputDivClass="col-sm-3" inputType="password" inputPlaceholder="Password" />
                    <FormButton buttonText="Sign in" clickAction={this.onLoginSubmit}
                                buttonClass="btn-default" divClass="col-sm-offset-2 col-sm2" />
                </form>
            </div>
            )}
});

var Loading = React.createClass({
    render: function() {
        return <div className="loading"></div>;
    }
});

var Nido = React.createClass({
    getInitialState: function() {
        return {
            view: 'loading',
            config: undefined,
            state: undefined,
            weather: undefined
        };
    },

    setView: function(state) {
        this.setState({
            view: state
        });
    },

    refreshServerState: function() {
        var that = this;
        var serverStates = ['config', 'state', 'weather'];

        for (let i = 0; i < serverStates.length; i++) {
            let serverState = serverStates[i];
            fetchData('get_' + serverState)
                .then(fetchCheckStatus2xx)
                .then(fetchResponseJSON)
                .then(function(json) {
                    let newState = {};
                    newState[serverState] = json;
                    that.setState(newState);
                })
                .catch(fetchGenericError);
        }
    },

    componentDidMount: function() {
        var that = this;
        // Get config server state and set view depending on response
        fetchData('get_config')
            .then(fetchCheckStatus2xx403)
            .then(function(response) {
                if ( response.status == 403 ) {
                    that.setView('login');
                    return Promise.resolve();
                } else {
                    return response.json();
                }
            })
            .then(function(json) {
                // Return if we got a 403 response
                if (json == undefined) return Promise.resolve();

                // Set config state
                that.setState({
                    config: json,
                    view: 'dashboard'
                });
            })
            .catch(fetchGenericError);
    },

    componentDidUpdate: function(prevProps, prevState) {
        if (prevState.view != this.state.view) {
            if (this.state.view != 'login') {
                this.refreshServerState();
            }
        }
        if ( prevState.config != this.state.config
             && this.state.config['config_required'] == true
             && this.state.view != 'config'
             ) {
            this.setView('config');
        }
    },
    
    render: function() {
        switch(this.state.view) {
            case 'loading':
                return <Loading />;
                break;
            case 'login':
                return <Login setView={this.setView} />;
                break;
            case 'dashboard':
                return <Dashboard setView={this.setView} config={this.state.config}
                                                         state={this.state.state}
                                                         weather={this.state.weather} />;
                break;
            case 'config':
                return <Config setView={this.setView} config={this.state.config} />;
                break;
            default:
                throw('Unexpected state was set in Nido component: ' + this.state.view);
        }
    }
});

ReactDOM.render(
  <Nido />,
  document.getElementById('nido')
);
