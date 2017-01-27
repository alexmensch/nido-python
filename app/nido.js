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
    // labelClass, inputDivClass, inputType, inputPlaceholder (string or list), labelText, inputId
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

var Dashboard = React.createClass({
    // Props: setView (function), config (JSON), state (JSON), weather (JSON), setConfig (function)
    render: function() {
        // Show Loading component unless we've received all props
        if ( this.props.config && this.props.state && this.props.weather ) {
            return(
                    <div id="dashboard">
                        <Toolbar setView={this.props.setView} />
                        <NidoState state={this.props.state} config={this.props.config} setConfig={this.props.setConfig} />
                        <Weather weather={this.props.weather} config={this.props.config} />
                    </div>
                );
        } else {
            return (
                <div id="dashboard">
                    <Loading />
                </div>
                );
        }
    }
});

var Toolbar = React.createClass({
    // Props: setView (function)
    homeawayAction: function() {
        return
    },

    configAction: function() {
        return
    },

    render: function() {
        return (
                <div id="toolbar">
                    <ToolbarButton icon={undefined} action={this.homeawayAction} />
                    <ToolbarButton icon={undefined} action={this.configAction} />
                </div>
                );
    }
});

var ToolbarButton = React.createClass({
    // Props: icon, action (function)
    render: function() {
        return (
            <div id="toolbarbutton">
                <span>{this.props.action.name} </span>;
            </div>
            );
    }
});

var NidoState = React.createClass({
    // Props: state (JSON), config (JSON), setConfig (function)
    render: function() {
        let rh = this.props.state.conditions.relative_humidity;
        return(
            <div>
                <div id="nidoState">
                    <Temperature temp={this.props.state.conditions.temp_c} celsius={this.props.config.celsius} />
                    <div className="rh">RH: {rh}%</div>
                </div>
                <div id="userControls">
                    <ChangeSetpoint config={this.props.config} />
                    <ChangeMode config={this.props.config} setConfig={this.props.setConfig} />
                </div>
            </div>
            );
    }
});

var Temperature = React.createClass({
    // Props: temp (float), celsius (boolean)
    c_to_f: function(temp) {
        let new_temp = ( ( temp * 9 ) / 5 ) + 32;
        return new_temp
    },

    round: function(temp) {
        return Math.round(temp)
    },

    render: function() {
        let display_temp = this.props.celsius ? this.props.temp : this.c_to_f(this.props.temp);
        display_temp = this.round(display_temp);
        return(
            <div className="temp">
                <span className="tempVal">{display_temp}</span>
                <span className="tempUnit">&deg;{this.props.celsius ? 'C' : 'F'}</span>
            </div>
            );
    }
});

var ChangeSetpoint = React.createClass({
    // Props: config (JSON)
    render: function() {
        return (
            <div id="changeSetpoint">
                <button type="button" className="btn">
                    <span className="glyphicon glyphicon-triangle-top">&nbsp;</span>
                </button>
                <button type="button" className="btn">
                    <span className="glyphicon glyphicon-triangle-bottom">&nbsp;</span>
                </button>
            </div>
            );
    }
});

var ChangeMode = React.createClass({
    // Props: config (JSON), setConfig (function)
    setMode: function(e) {
        let newMode = '';
        // Find current mode in list of available modes and increment
        for(let i = 0; i < this.props.config.modes.length; i++) {
            if (this.props.config.mode_set == this.props.config.modes[i]) {
                newMode = this.props.config.modes[((i+1) % this.props.config.modes.length)];
            }
        }

        // Set new mode
        this.props.setConfig({
            mode_set: newMode
        });

        return
    },

    render: function() {
        return (
            <div id="changeMode">
                <Temperature temp={this.props.config.set_temperature} celsius={this.props.config.celsius} />
                <ShowMode action={this.setMode} mode={this.props.config.mode_set} />
            </div>
            );
    }
});

var ShowMode = React.createClass({
    // Props: mode (string), action (function)
    render: function() {
        switch(this.props.mode) {
            case 'Off':
                return (
                    <div id="showMode" onClick={this.props.action}>
                        <span>OFF</span>
                    </div>
                    );
                break;
            case 'Heat':
                return (
                    <div id="showMode" onClick={this.props.action}>
                        <span className="glyphicon glyphicon-fire">&nbsp;</span>
                    </div>
                    );
                break;
            case 'Cool':
                return (
                    <div id="showMode" onClick={this.props.action}>
                        <span className="glyphicon glyphicon-asterisk">&nbsp;</span>
                    </div>
                    );
                break;
            case 'Heat_Cool':
                return (
                    <div id="showMode" onClick={this.props.action}>
                        <span className="glyphicon glyphicon-fire">&nbsp;</span>
                        <span className="glyphicon glyphicon-asterisk">&nbsp;</span>
                    </div>
                    );
                break;
            default:
                return (
                    <div id="showMode" onClick={this.props.action}>
                        <span className="glyphicon glyphicon-flash">&nbsp;</span>
                    </div>
                    );
        }
    }
});

var Weather = React.createClass({
    // Props: weather (JSON), config (JSON)
    render: function() {
        return(
            <div id="weather">
                <WeatherIcon icon={this.props.weather.condition.icon_url} />
                <Temperature temp={this.props.weather.temp_c} celsius={this.props.config.celsius} />
                <TempHighLow />
                <SunriseSunset />
            </div>
            );
    }
});

var WeatherIcon = React.createClass({
    // Props: icon (string)
    render: function() {
        return <div>Weather icon</div>;
    }
});

var TempHighLow = React.createClass({
    // Props: ?
    render: function() {
        return <div>High / Low</div>;
    }
});

var SunriseSunset = React.createClass({
    // Props: ?
    render: function() {
        return <div>Sunrise / Sunset</div>;
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
            if (json.logged_in == true) {
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

    setConfig: function(newConfig) {
        let that = this;
        fetch('/set_config', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            credentials: 'include',
            body: JSON.stringify(newConfig)
        })
        .then(fetchCheckStatus2xx)
        .then(fetchResponseJSON)
        .then(function(json) {
            // TODO: Show 'message' and 'error' content to user as appropriate
            if (json.config) {
                let newState = {};
                newState.config = json.config;
                that.setState(newState);
            }
        }).catch(fetchGenericError);
    },

    refreshServerState: function() {
        let that = this;
        let serverStates = ['config', 'state', 'weather'];

        // Initiate async requests to the list of endpoints
        for (let i = 0; i < serverStates.length; i++) {
            let serverState = serverStates[i];
            fetchData('get_' + serverState)
                .then(fetchCheckStatus2xx)
                .then(fetchResponseJSON)
                .then(function(json) {
                    let newState = {};
                    newState[serverState] = json[serverState];
                    that.setState(newState);
                })
                .catch(fetchGenericError);
        }
    },

    componentDidMount: function() {
        var that = this;
        // Make a call to get_config to see if the user is logged in already
        fetchData('get_config')
            .then(fetchCheckStatus2xx403)
            .then(function(response) {
                if ( response.status == 403 ) {
                    that.setView('login');
                } else {
                    that.setView('dashboard');
                }
                return Promise.resolve();
            })
            .catch(fetchGenericError);
    },

    componentDidUpdate: function(prevProps, prevState) {
        // Refresh data from server any time we change state,
        // except when we've moved into the login state
        if (prevState.view != this.state.view) {
            if (this.state.view != 'login') {
                this.refreshServerState();
            }
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
                return <Dashboard setView={this.setView} setConfig={this.setConfig}
                                  config={this.state.config}
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
