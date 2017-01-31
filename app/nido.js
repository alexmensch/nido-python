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
    // buttonText, clickAction (func), buttonClass, divClass, submit (boolean)
    render: function() {
        let type = this.props.submit ? 'submit' : 'button';
        return (
            <div className="form-group">
                <div className={this.props.divClass}>
                    <button type={type} onClick={this.props.clickAction}
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
    onConfigSubmit: function(e) {
        e.preventDefault();
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
                                    buttonClass="btn-primary" divClass="col-sm-offset-2 col-sm-2"
                                    submit={true} />
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
                        <Weather weather={this.props.weather} config={this.props.config} setConfig={this.props.setConfig} />
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
                    <TempRHToggle celsius={this.props.config.celsius}
                                  temp={this.props.state.conditions.temp_c}
                                  rh={this.props.state.conditions.relative_humidity}
                                  setConfig={this.props.setConfig} />
                </div>
                <div id="userControls">
                    <ChangeSetpoint config={this.props.config} setConfig={this.props.setConfig} />
                    <ChangeMode config={this.props.config} setConfig={this.props.setConfig} />
                </div>
            </div>
            );
    }
});

var ChangeSetpoint = React.createClass({
    // Props: config (JSON), setConfig (function)
    f_to_c: function(temp) {
        let new_temp = ( ( temp - 32 ) * 5 ) / 9;
        return new_temp
    },

    changeSetpoint: function(increment) {
        let newTemp = this.props.config.set_temperature;
        if (this.props.config.celsius) {
            newTemp += increment ? 0.5 : -0.5;
        } else {
            newTemp += increment ? 0.5555 : -0.5555;
        }
        this.props.setConfig({
            set_temperature: newTemp
        });

        return
    },

    increment: function(e) {
        e.preventDefault();
        this.changeSetpoint(true);
        return
    },

    decrement: function(e) {
        e.preventDefault();
        this.changeSetpoint(false);
        return
    },

    render: function() {
        return (
            <div id="changeSetpoint">
                <div id="incrementTemp" onClick={this.increment} >
                    <span className="glyphicon glyphicon-triangle-top">&nbsp;</span><br />
                </div>
                <div id="decrementTemp" onClick={this.decrement} >
                    <span className="glyphicon glyphicon-triangle-bottom">&nbsp;</span>
                </div>
            </div>
            );
    }
});

var ChangeMode = React.createClass({
    // Props: config (JSON), setConfig (function)
    setMode: function(e) {
        e.preventDefault();
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
                <Temperature temp={this.props.config.set_temperature} celsius={this.props.config.celsius}
                             setConfig={this.props.setConfig} />
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
    // Props: weather (JSON), config (JSON), setConfig (function)
    render: function() {
        return(
            <div id="weather">
                <WeatherIcon icon={this.props.weather.condition.icon_url} alt={this.props.weather.condition.description}/>
                <TempRHToggle celsius={this.props.config.celsius}
                              temp={this.props.weather.temp_c}
                              rh={this.props.weather.relative_humidity}
                              setConfig={this.props.setConfig} />
                <TempHighLow high={this.props.weather.forecast.high} low={this.props.weather.forecast.low}
                             celsius={this.props.config.celsius} setConfig={this.props.setConfig} />
                <SunriseSunset sunrise={this.props.weather.solar.sunrise} sunset={this.props.weather.solar.sunset} />
            </div>
            );
    }
});

var WeatherIcon = React.createClass({
    // Props: icon (string), alt (string)
    render: function() {
        return (
            <div className="weatherIcon">
                <img src={this.props.icon} alt={this.props.alt}/>
            </div>
            );
    }
});

var TempRHToggle = React.createClass({
    // Props: temp (float), rh (float), celsius (boolean), setConfig (function)
    getInitialState: function() {
        return {
            temp: true,
        };
    },

    toggleDisplay: function(e) {
        e.preventDefault();
        this.setState({
            temp: !this.state.temp
        });
    },

    render: function() {
        if (this.state.temp) {
            return (
                <div className="tempRHToggle">
                    <Temperature temp={this.props.temp} celsius={this.props.celsius}
                                 setConfig={this.props.setConfig}
                                 toggleAction={this.toggleDisplay} />
                </div>
                );
        } else {
            return (
                <div className="tempRHToggle" onClick={this.toggleDisplay}>
                    <RH rh={this.props.rh} />
                </div>
                );
        }
    }
});

var Temperature = React.createClass({
    // Props: temp (float), celsius (boolean), setConfig (function), toggleAction (function)
    c_to_f: function(temp) {
        let new_temp = ( ( temp * 9 ) / 5 ) + 32;
        return new_temp
    },

    round: function(temp) {
        let multiplier = this.props.celsius ? Math.pow(10, 1) : Math.pow(10, 0);
        let result = Math.round(temp * multiplier) / multiplier;

        return this.props.celsius ? result.toFixed(1) : result.toFixed(0);
    },

    toggleUnit: function(e) {
        e.preventDefault();
        this.props.setConfig({
            celsius: !this.props.celsius
        });
        return
    },

    render: function() {
        let display_temp = this.props.celsius ? this.props.temp : this.c_to_f(this.props.temp);
        display_temp = this.round(display_temp);
        return(
            <div className="temp">
                <span className="tempVal" onClick={this.props.toggleAction}>{display_temp}</span>
                <span className="tempUnit" onClick={this.toggleUnit}>&deg;{this.props.celsius ? 'C' : 'F'}</span>
            </div>
            );
    }
});

var RH = React.createClass({
    // Props: rh (float)
    render: function() {
        let rhDisplay = Math.round(this.props.rh);
        return (
            <div className="rh">
                <span className="rhVal">{rhDisplay}%</span>
            </div>
            );
    }
});

var TempHighLow = React.createClass({
    // Props: high (string), low (string), celsius (boolean), setConfig (function)
    render: function() {
        return (
            <div className="tempHighLow">
                H: <Temperature temp={this.props.high} celsius={this.props.celsius} setConfig={this.props.setConfig} />
                L: <Temperature temp={this.props.low} celsius={this.props.celsius} setConfig={this.props.setConfig} />
            </div>
            );
    }
});

var SunriseSunset = React.createClass({
    // Props: sunrise (int), sunset (int)
    render: function() {
        let now = new Date();
        let nowHrMin = (now.getHours() * 100) + now.getMinutes();
        let nextChange = 'Sun';

        if (nowHrMin > this.props.sunrise && nowHrMin < this.props.sunset) {
            let hour = this.props.sunset.toString().slice(-4,-2);
            let min = this.props.sunset.toString().slice(-2);
            nextChange += 'set: ' + hour + ":" + min;
        } else {
            let hour = this.props.sunrise.toString().slice(-4,-2);
            let min = this.props.sunrise.toString().slice(-2);
            nextChange += 'rise: ' + hour + ":" + min;
        }

        return <div className="sunriseSunset">{nextChange}</div>;
    }
});

var Login = React.createClass({
    // Login: setView (function)
    onLoginSubmit: function(e) {
        e.preventDefault();
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
                                buttonClass="btn-primary" divClass="col-sm-offset-2 col-sm2"
                                submit={true} />
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
