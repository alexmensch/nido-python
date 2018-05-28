/* ********
 *   Nido, a Raspberry Pi-based home thermostat.
 *
 *   Copyright (C) 2016 Alex Marshall
 *
 *   This program is free software: you can redistribute it and/or modify
 *   it under the terms of the GNU General Public License as published by
 *   the Free Software Foundation, either version 3 of the License, or
 *   (at your option) any later version.
 *
 *   This program is distributed in the hope that it will be useful,
 *   but WITHOUT ANY WARRANTY; without even the implied warranty of
 *   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 *   GNU General Public License for more details.
 *
 *   You should have received a copy of the GNU General Public License
 *   along with this program.  If not, see <http://www.gnu.org/licenses/>.
 * ********
 */

import React from 'react'
import ReactDOM from 'react-dom'
// import polyfill from 'es6-promise'
import * as Icon from './icons'
import fetch from 'isomorphic-fetch'
import Geosuggest from 'react-geosuggest'

/* ********
 * fetch() helper functions for Promise then-chain processing
 * ********
 */

function fetchCheckStatus2xx (response) {
  if (response.status >= 200 && response.status < 300) {
    return Promise.resolve(response)
  } else {
    return Promise.reject(new Error(response.statusText))
  }
}

function fetchCheckStatus2xx403 (response) {
  if (response.status === 403 ||
    (response.status >= 200 && response.status < 300)) {
    return Promise.resolve(response)
  } else {
    return Promise.reject(new Error(response.statusText))
  }
}

function fetchResponseJSON (response) {
  return response.json()
}

function fetchGenericError (error) {
  console.log('Request failed: ', error)
}

/* ********
 * fetch() calls
 * ********
 */

function fetchData (route) {
  return fetch('/' + route, {
    method: 'POST',
    credentials: 'include'
  })
    .catch(fetchGenericError)
}

/* ********
 * Temperature functions
 * Source: https://facebook.github.io/react/docs/lifting-state-up.html
 * ********
 */

// Note: returns a string!
function roundDecimal (value, decimals) {
  const result = Math.round(value * Math.pow(10, decimals)) / Math.pow(10, decimals)
  return result.toFixed(decimals)
}

function roundStep (value, step) {
  step || (step = 1.0)
  var inv = 1.0 / step
  return Math.round(value * inv) / inv
}

function toCelsius (fahrenheit) {
  const result = (fahrenheit - 32) * 5 / 9
  return roundDecimal(result, 1)
}

function toFahrenheit (celsius) {
  const result = (celsius * 9 / 5) + 32
  return roundDecimal(result, 0)
}

function tryConvert (value, convert) {
  const input = parseFloat(value)
  if (Number.isNaN(input)) {
    return ''
  }
  return convert(input)
}

/* ********
 * Misc helper functions
 * ********
 */

function compareState (cur, prev) {
  for (let property in cur) {
    if (cur.hasOwnProperty(property)) {
      if (cur[property] !== prev[property]) {
        return false
      }
    }
  }
  return true
}

/* ********
 * React components (Content)
 * ********
 */

class Dashboard extends React.Component {
    /* Props:
      setView (function),
      config (JSON),
      state (JSON),
      weather (JSON),
      setConfig (function)
    */
  constructor (props) {
    super(props)
    this.handleTempUnitChange = this.handleTempUnitChange.bind(this)
    this.handleModeChange = this.handleModeChange.bind(this)
    this.handleSetpointChange = this.handleSetpointChange.bind(this)
  }

  /* We save this state and handle changes in this component so that we have a single
    point from which we coordinate updating the server via the /set_config endpoint
  */
  componentWillReceiveProps (nextProps) {
    if (nextProps.config !== undefined) {
      // NOTE: temperature received from server is always in Celsius
      this.setState({
        celsius: nextProps.config.celsius,
        set_temp: nextProps.config.set_temperature,
        set_mode: nextProps.config.mode_set
      })
    }
  }

  componentDidUpdate (prevProps, prevState) {
    // To avoid a large number of API calls, we set a timeout that gets
    // reset every time a state change occurs. Once the timeout expires,
    // an update is sent to the server to make server state consistent
    // with this component.
    if (prevState !== undefined && !compareState(this.state, prevState)) {
      if (typeof this.timerID === 'number') {
        clearTimeout(this.timerID)
        this.timerID = undefined
      } else {
        this.serverState = prevState
      }
      this.timerID = setTimeout(
        () => {
          if (!compareState(this.state, this.serverState)) {
            this.props.setConfig(this.state)
          }
          this.timerID = undefined
          this.serverState = undefined
        },
        1500
      )
    }
  }

  componentWillUnmount () {
    if (typeof this.timerID === 'number') {
      clearTimeout(this.timerID)
      if (!compareState(this.state, this.serverState)) {
        this.props.setConfig(this.state)
      }
    }
  }

  handleTempUnitChange () {
    const newScale = !this.state.celsius
    let newTemp = this.state.set_temperature

    if (newScale) {
      newTemp = roundStep(newTemp, 0.5)
    } else {
      newTemp = tryConvert(newTemp, toFahrenheit)
      newTemp = roundStep(newTemp, 1.0)
      newTemp = tryConvert(newTemp, toCelsius)
    }

    this.setState({
      celsius: newScale,
      set_temp: Number(newTemp)
    })
  }

  handleSetpointChange (increment) {
    const scale = this.state.celsius
    let newTemp = this.state.set_temperature

    if (scale) {
      newTemp = roundStep(newTemp, 0.5)
      newTemp += increment ? 0.5 : -0.5
    } else {
      newTemp = tryConvert(newTemp, toFahrenheit)
      newTemp = roundStep(newTemp, 1.0)
      newTemp += increment ? 1 : -1
      newTemp = tryConvert(newTemp, toCelsius)
    }
    this.setState({
      set_temp: Number(newTemp)
    })
  }

  handleModeChange () {
    let newMode
        // Find current mode in list of available modes and increment
    for (let i = 0; i < this.props.config.modes.length; i++) {
      if (this.state.mode_set === this.props.config.modes[i]) {
        newMode = this.props.config.modes[((i + 1) % this.props.config.modes.length)]
      }
    }

    this.setState({
      set_mode: newMode
    })
  }

  render () {
    // Show Loading component unless we've received all props
    if (this.props.config && this.props.state && this.props.weather) {
      const scale = this.state.celsius
      const unit = scale ? 'C' : 'F'
      const settemp = roundDecimal(this.state.set_temperature, 1)
      const sensortemp = roundDecimal(this.props.state.conditions.temp_c, 1)
      const weathertemp = roundDecimal(this.props.weather.temp_c, 1)
      const hightemp = roundDecimal(this.props.weather.forecast.high, 1)
      const lowtemp = roundDecimal(this.props.weather.forecast.low, 1)

      return (
        <div id='dashboard'>
          <Toolbar setView={this.props.setView} />
          <NidoState>
            <TempRHToggle unit={unit}
              temp={scale ? sensortemp : tryConvert(sensortemp, toFahrenheit)}
              rh={this.props.state.conditions.relative_humidity}
              toggleUnit={this.handleTempUnitChange} />
            <ControlSetpoint changeSetpoint={this.handleSetpointChange} />
            <ControlMode changeMode={this.handleModeChange}
              toggleUnit={this.handleTempUnitChange}
              mode={this.state.mode_set} temp={scale
                ? settemp
                : tryConvert(settemp, toFahrenheit)}
              unit={unit} />
          </NidoState>
          <Weather>
            <WeatherIcon icon={this.props.weather.condition.icon_url}
              alt={this.props.weather.condition.description} />
            <TempRHToggle unit={unit}
              temp={scale ? weathertemp : tryConvert(weathertemp, toFahrenheit)}
              rh={this.props.weather.relative_humidity}
              toggleUnit={this.handleTempUnitChange} />
            <TempHighLow high={scale ? hightemp : tryConvert(hightemp, toFahrenheit)}
              low={scale ? lowtemp : tryConvert(lowtemp, toFahrenheit)}
              unit={unit} toggleUnit={this.handleTempUnitChange} />
            <SunriseSunset sunrise={this.props.weather.solar.sunrise}
              sunset={this.props.weather.solar.sunset} />
          </Weather>
        </div>
      )
    } else {
      return (
        <div id='dashboard'>
          <Loading />
        </div>
      )
    }
  }
}

class Toolbar extends React.Component {
    // Props: setView (function)
  constructor (props) {
    super(props)
    this.handleConfigClick = this.handleConfigClick.bind(this)
  }

  handleConfigClick (e) {
    e.preventDefault()
    this.props.setView('config')
  }

  render () {
    return (
      <div id='toolbar'>
        <ToolbarButton action={this.handleConfigClick}>
          <Icon.Cogs />
        </ToolbarButton>
      </div>
    )
  }
}

function ToolbarButton (props) {
    // Props: icon, action (function)
  return (
    <div className='toolbarbutton' onClick={props.action}>
      {props.children}
    </div>
  )
}

function NidoState (props) {
    // Props: none
  return (
    <div id='nidoState'>
      {props.children}
    </div>
  )
}

class ControlSetpoint extends React.Component {
    // Props: changeSetpoint (function)
  constructor (props) {
    super(props)
    this.handleIncrement = this.handleIncrement.bind(this)
    this.handleDecrement = this.handleDecrement.bind(this)
  }

  handleIncrement (e) {
    e.preventDefault()
    this.props.changeSetpoint(true)
  }

  handleDecrement (e) {
    e.preventDefault()
    this.props.changeSetpoint(false)
  }

  render () {
    return (
      <div id='changeSetpoint'>
        <div id='incrementTemp' onClick={this.handleIncrement} >
          <Icon.CircleUp />
        </div>
        <div id='decrementTemp' onClick={this.handleDecrement} >
          <Icon.CircleDown />
        </div>
      </div>
    )
  }
}

function ControlMode (props) {
    // Props: changeMode (function), mode (string), temp (float), unit (string), toggleUnit (function)
  return (
    <div id='changeMode'>
      <Temperature temp={props.temp} unit={props.unit}
        toggleUnit={props.toggleUnit} />
      <ShowMode action={props.changeMode} mode={props.mode} />
    </div>
  )
}

class ShowMode extends React.Component {
  // Props: mode (string), action (function)

  modeDisplay (mode) {
    switch (mode) {
      case 'Off':
        return <Icon.Switch />
      case 'Heat':
        return <Icon.Fire />
      case 'Cool':
        return
      case 'Heat_Cool':
        return (
          <div>
            <Icon.Fire />
            <object type='image/svg+xml' data='static/svg/weather/7.svg'
              id='mode-cool' className='svg-wrapper'>Cool</object>
          </div>
        )
      default:
        return (
          <object type='image/svg+xml' data='static/svg/weather/45.svg'
            id='mode-na' className='svg-wrapper'>N/A</object>
        )
    }
  }

  render () {
    return (
      <div id='showMode' onClick={this.props.action}>
        {this.modeDisplay(this.props.mode)}
      </div>
    )
  }
}

function Weather (props) {
  // Props: none
  return (
    <div id='weather'>
      {props.children}
    </div>
  )
}

function WeatherIcon (props) {
  // Props: icon (string), alt (string)
  return (
    <div className='weatherIcon'>
      <img src={props.icon} alt={props.alt} />
    </div>
  )
}

class TempRHToggle extends React.Component {
  // Props: temp (float), rh (float), unit (string), toggleUnit (function)
  constructor (props) {
    super(props)
    this.state = {
      temp: true
    }
    this.handleToggleDisplay = this.handleToggleDisplay.bind(this)
  }

  handleToggleDisplay (e) {
    e.preventDefault()
    this.setState({
      temp: !this.state.temp
    })
  }

  temperature () {
    return (
      <Temperature temp={this.props.temp} unit={this.props.unit}
        toggleUnit={this.props.toggleUnit}
        toggleAction={this.handleToggleDisplay} />
    )
  }

  rh () {
    return (
      <RH rh={this.props.rh} toggleAction={this.handleToggleDisplay} />
    )
  }

  render () {
    return (
      <div className='tempRHToggle'>
        {this.state.temp ? this.temperature() : this.rh()}
      </div>
    )
  }
}

function Temperature (props) {
    // Props: temp (float), unit (string), toggleAction (function), toggleUnit (function)
  return (
    <div className='temperature'>
      <span className='tempVal' onClick={props.toggleAction}>{props.temp}</span>
      <span className='tempUnit' onClick={props.toggleUnit}>&deg;{props.unit}</span>
    </div>
  )
}

function RH (props) {
    // Props: rh (float), toggleAction (function)
  let rhDisplay = roundDecimal(props.rh, 0)
  return (
    <div className='rh' onClick={props.toggleAction}>
      <span className='rhVal'>{rhDisplay}%</span>
    </div>
  )
}

function TempHighLow (props) {
    // Props: high (string), low (string), unit (string), toggleUnit (function)
  return (
    <div className='tempHighLow'>
            H: <Temperature temp={props.high} unit={props.unit}
              toggleUnit={props.toggleUnit} />
            L: <Temperature temp={props.low} unit={props.unit}
              toggleUnit={props.toggleUnit} />
    </div>
  )
}

class SunriseSunset extends React.Component {
  // Props: sunrise (int), sunset (int)
  nextTransition () {
    let now = new Date()
    let nowHrMin = (now.getHours() * 100) + now.getMinutes()

    if (nowHrMin > this.props.sunrise && nowHrMin < this.props.sunset) {
      let hour = this.props.sunset.toString().slice(-4, -2)
      let min = this.props.sunset.toString().slice(-2)
      return (
        <div>
          <Icon.Sunset />
          <span id='sunriseSunsetTime'>{hour + ':' + min}</span>
        </div>
      )
    } else {
      let hour = this.props.sunrise.toString().slice(-4, -2)
      let min = this.props.sunrise.toString().slice(-2)
      return (
        <div>
          <Icon.Sunrise />
          <span id='sunriseSunsetTime'>{hour + ':' + min}</span>
        </div>
      )
    }
  }

  render () {
    return <div className='sunriseSunset'>{this.nextTransition()}</div>
  }
}

class Login extends React.Component {
    // Login: setView (function)
  constructor (props) {
    super(props)
    this.handleLoginSubmit = this.handleLoginSubmit.bind(this)
  }

  handleLoginSubmit (e) {
    e.preventDefault()
    let form = new FormData()
    form.append('username', document.getElementById('input-Username').value)
    form.append('password', document.getElementById('input-Password').value)

    let that = this
    fetch('/login', {
      method: 'POST',
      body: form,
      credentials: 'include'
    })
    .then(fetchCheckStatus2xx)
    .then(fetchResponseJSON)
    .then(function (json) {
    // TODO: Incorporate message/error text into user feedback.
      if (json.logged_in === true) {
        that.props.setView('dashboard')
      }
    })
    .catch(fetchGenericError)
  }

  render () {
    return (
      <ShowForm formId='login' title='Login'
        submitAction={this.handleLoginSubmit}>
        <FormRow labelText='Username' inputId='input-Username'>
          <FormText inputId='input-Username' placeholder='Username' />
        </FormRow>
        <FormRow labelText='Password' inputId='input-Password'>
          <FormText password
            inputId='input-Password' placeholder='Password' />
        </FormRow>
        <FormSubmitButton buttonText='Sign in' buttonClass='btn-primary'
          divClass='col-sm-offset-2 col-sm2' />
      </ShowForm>
    )
  }
}

class Config extends React.Component {
    // Props: setView (function), config (JSON)
  constructor (props) {
    super(props)
    this.state = {
      location: undefined
    }

    this.handleConfigSubmit = this.handleConfigSubmit.bind(this)
    this.handleLocationSelect = this.handleLocationSelect.bind(this)
  }

  handleConfigSubmit (e) {
    e.preventDefault()
  }

  handleLocationSelect (selection) {

  }

  render () {
    const locationLabel = 'location_label' in this.props.config
      ? this.props.config.location_label
      : false
    return (
      <ShowForm formId='config' title='Configuration'
        submitAction={this.handleConfigSubmit}>
        <FormRow inputId='location' labelText='Location'>
          <Geosuggest placeholder={locationLabel || 'Your location'}
            onSuggestSelect={this.handleLocationSelect} />
        </FormRow>
        <FormRow inputId='modes' LabelText='Available modes'>
          {this.props.config.modes_available.map((item) =>
            <FormCheckbox inputId={'modes-' + item[0]} label={item[0]}
              checked={item[1]} />
          )}
        </FormRow>
        <FormSubmitButton buttonText='Save'
          buttonClass='btn-primary' divClass='col-sm-offset-2 col-sm-2' />
      </ShowForm>
    )
  }
}

function ShowForm (props) {
  return (
    <div className='form' id={props.formId}>
      <h2>{props.title}</h2>
      <form className='form-horizontal' onSubmit={props.submitAction}>
        {props.children}
      </form>
    </div>
  )
}

function FormRow (props) {
    // Props: inputId, labelText
  return (
    <div className='form-group'>
      <label htmlFor={props.inputId} className='control-label'>
        {props.labelText}
      </label>
      <div className='inputDiv'>
        {props.children}
      </div>
    </div>
  )
}

function FormCheckbox (props) {
    // Props: inputId (string), data (list of tuples)
  return (
    <div className={props.inputId} key={props.data[0]}>
      <label>
        <input type='checkbox' id={props.inputId + '-' + props.data[0]}
          value={props.data[0]} defaultChecked={props.data[1]} />
        {props.data[0]}
      </label>
    </div>
  )
}

function FormText (props) {
    // Props: inputId (string), placeholder (string), password (boolean, default false)
  return (
    <input type={props.password ? 'password' : 'text'} className='form-control'
      id={props.inputId} placeholder={props.placeholder} />
  )
}
FormText.defaultProps = { password: false }
FormText.propTypes = { password: React.PropTypes.bool }

function FormSubmitButton (props) {
    // Props: buttonText, buttonClass, divClass
  return (
    <div className='form-group'>
      <div className={props.divClass}>
        <button type='submit' className={'btn ' + props.buttonClass}>
          {props.buttonText}
        </button>
      </div>
    </div>
  )
}

function Loading (props) {
  return <div className='loading' />
}

class Nido extends React.Component {
  constructor (props) {
    super(props)
    this.state = {
      view: 'loading',
      config: undefined,
      state: undefined,
      weather: undefined
    }
    this.setView = this.setView.bind(this)
    this.setConfig = this.setConfig.bind(this)
  }

  setView (state) {
    this.setState({
      view: state
    })
  }

  setConfig (newConfig) {
    let that = this
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
    .then(function (json) {
    // TODO: Show 'message' and 'error' content to user as appropriate
      if (json.config) {
        let newState = {}
        newState.config = json.config
        that.setState(newState)
      }
    })
    .catch(fetchGenericError)
  }

  refreshServerState () {
    let that = this
    let serverStates = ['config', 'state', 'weather']

    // Initiate async requests to the list of endpoints
    for (let i = 0; i < serverStates.length; i++) {
      let serverState = serverStates[i]
      fetchData('get_' + serverState)
      .then(fetchCheckStatus2xx)
      .then(fetchResponseJSON)
      .then(function (json) {
        let newState = {}
        newState[serverState] = json[serverState]
        that.setState(newState)
      })
      .catch(fetchGenericError)
    }
  }

  componentDidMount () {
    let that = this
    // Make a call to get_config to see if the user is logged in already
    fetchData('get_config')
    .then(fetchCheckStatus2xx403)
    .then(function (response) {
      if (response.status === 403) {
        that.setView('login')
      } else {
        that.setView('dashboard')
      }
      return Promise.resolve()
    })
    .catch(fetchGenericError)
    // Set up an interval timer to update the UI
    // 360,000ms = 6min = 10/hr
    this.timerID = setInterval(
      () => {
        if (this.state.view === 'dashboard') {
          this.refreshServerState()
        }
      },
      360000
    )
  }

  componentDidUpdate (prevProps, prevState) {
    // Refresh data from server any time we change state,
    // except when we've moved into the login state
    if (prevState.view !== this.state.view) {
      if (this.state.view !== 'login') {
        this.refreshServerState()
      }
    }
  }

  componentWillUnmount () {
    clearInterval(this.timerID)
  }

  render () {
    switch (this.state.view) {
      case 'loading':
        return <Loading />
      case 'login':
        return <Login setView={this.setView} />
      case 'dashboard':
        return (
          <Dashboard setView={this.setView} setConfig={this.setConfig}
            config={this.state.config}
            state={this.state.state}
            weather={this.state.weather} />
        )
      case 'config':
        return <Config setView={this.setView} config={this.state.config} />
    }
  }
}

ReactDOM.render(
  <Nido />,
  document.getElementById('nido')
)
