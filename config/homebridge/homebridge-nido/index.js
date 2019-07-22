/*
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
 *   along with this program.
 *   If not, see <http://www.gnu.org/licenses/>.
 */

var Service, Characteristic;

module.exports = function (homebridge) {
  Service = homebridge.hap.Service;
  Characteristic = homebridge.hap.Characteristic;
  homebridge.registerAccessory("homebridge-nido", "NidoThermostat", NidoThermostat);
};

const request = require('request');
const url = require('url');

/**
 * Service "Thermostat"
 ***
 * Reference:
 * https://github.com/KhaosT/HAP-NodeJS/blob/master/lib/gen/HomeKitTypes.js#L3439
 ***

Service.Thermostat = function(displayName, subtype) {
  Service.call(this, displayName, '0000004A-0000-1000-8000-0026BB765291', subtype);

  // Required Characteristics
  this.addCharacteristic(Characteristic.CurrentHeatingCoolingState);            R
  this.addCharacteristic(Characteristic.TargetHeatingCoolingState);             R, W
  this.addCharacteristic(Characteristic.CurrentTemperature);                    R
  this.addCharacteristic(Characteristic.TargetTemperature);                     R, W
  this.addCharacteristic(Characteristic.TemperatureDisplayUnits);               R, W

  // Optional Characteristics
  this.addOptionalCharacteristic(Characteristic.CurrentRelativeHumidity);       R
  this.addOptionalCharacteristic(Characteristic.TargetRelativeHumidity);        [n/a]
  this.addOptionalCharacteristic(Characteristic.CoolingThresholdTemperature);   [n/a]
  this.addOptionalCharacteristic(Characteristic.HeatingThresholdTemperature);   [n/a]
  this.addOptionalCharacteristic(Characteristic.Name);                          [n/a]
};

inherits(Service.Thermostat, Service);

Service.Thermostat.UUID = '0000004A-0000-1000-8000-0026BB765291';

 *
 **/

NidoThermostat.prototype = {
  getServices: function () {
    let informationService = new Service.AccessoryInformation();
    informationService
      .setCharacteristic(Characteristic.Manufacturer, "Moveo Labs")
      .setCharacteristic(Characteristic.Model, "Nido v1")
      .setCharacteristic(Characteristic.SerialNumber, "1");

    let thermostatService = new Service.Thermostat("Nido");
    thermostatService
      .getCharacteristic(Characteristic.CurrentHeatingCoolingState)
        .on('get', this.getCurrentHeatingCoolingState.bind(this));
    thermostatService
      .getCharacteristic(Characteristic.TargetHeatingCoolingState)
        .on('get', this.getTargetHeatingCoolingState.bind(this))
        .on('set', this.setTargetHeatingCoolingState.bind(this));
    thermostatService
      .getCharacteristic(Characteristic.CurrentTemperature)
        .on('get', this.getCurrentTemperature.bind(this));
    thermostatService
      .getCharacteristic(Characteristic.TargetTemperature)
        .on('get', this.getTargetTemperature.bind(this))
        .on('set', this.setTargetTemperature.bind(this));
    thermostatService
      .getCharacteristic(Characteristic.TemperatureDisplayUnits)
        .on('get', this.getTemperatureDisplayUnits.bind(this))
        .on('set', this.setTemperatureDisplayUnits.bind(this));
    thermostatService
      .getCharacteristic(Characteristic.CurrentRelativeHumidity)
        .on('get', this.getCurrentRelativeHumidity.bind(this));

    this.informationService = informationService;
    this.thermostatService = thermostatService;
    return [informationService, thermostatService];
  },

  getCurrentHeatingCoolingState: function (callback) {
    const me = this;
    const config = {
      ...me.requestConfig,
      ...{ url: me.getCHCSUrl }
    };

    request(
      config, 
      function (error, response, body) {
        if (error) { me.errorHandler(me, callback, error, response); }
        const r = JSON.parse(body);
        return callback(null, r.state.value);
      }
    );
  },

  getTargetHeatingCoolingState: function (callback) {
    const me = this;
    const config = {
      ...me.requestConfig,
      ...{ url: me.getTHCSUrl }
    };

    request(
      config,
      function (error, response, body) {
        if (error) { me.errorHandler(me, callback, error, response); }
        const r = JSON.parse(body);
        return callback(null, r.mode.value);
      }
    );
  },

  setTargetHeatingCoolingState: function (set, callback) {
    const me = this;
    const setVal = me.modeMap[set]
    const setUrl = me.setTHCSUrl.pathname(me.setTHCSUrl.pathname + setVal);
    const config = {
        ...me.requestConfig,
        ...{ url: setUrl }
    };

    me.issueRequest(me, config, callback);
  },

  getCurrentTemperature: function (callback) {
    const me = this;
    const config = {
      ...me.requestConfig,
      ...{ url: me.getCTUrl }
    };

    request(
      config,
      function (error, response, body) {
        if (error) { me.errorHandler(me, callback, error, response); }
        const r = JSON.parse(body);
        return callback(null, r.conditions.temp_c);
      }
    );
  },

  getTargetTemperature: function (callback) {
    const me = this;
    const config = {
      ...me.requestConfig,
      ...{ url: me.getTTUrl }
    };

    request(
      config,
      function (error, response, body) {
        if (error) { me.errorHandler(me, callback, error, response); }
        const r = JSON.parse(body);
        return callback(null, r.temp.celsius);
      }
    );
  },

  setTargetTemperature: function (set, callback) {
    const me = this;
    const setUrl = me.setTTUrl.pathname(me.setTHCSUrl.pathname + set + '/C');
    const config = {
        ...me.requestConfig,
        ...{ url: setUrl }
    };

    me.issueRequest(me, config, callback);
  },

  getTemperatureDisplayUnits: function (callback) {
    const me = this;
    const config = {
      ...me.requestConfig,
      ...{ url: me.getTDUUrl }
    };

    request(
      config,
      function (error, response, body) {
        if (error) { me.errorHandler(me, callback, error, response); }
        const r = JSON.parse(body);
        return callback(null, r.celsius ? 1 : 0);
      }
    );
  },

  setTemperatureDisplayUnits: function (set, callback) {
    const me = this;
    const setVal = set ? 'C' : 'F';
    const setUrl = me.setTDUUrl.pathname(me.setTHCSUrl.pathname + setVal);
    const config = {
        ...me.requestConfig,
        ...{ url: setUrl }
    };

    me.issueRequest(me, config, callback);  
  },

  getCurrentRelativeHumidity: function (callback) {
    const me = this;
    const config = {
      ...me.requestConfig,
      ...{ url: me.getCRHUrl }
    };

    request(
      config,
      function (error, response, body) {
        if (error) { me.errorHandler(me, callback, error, response); }
        const r = JSON.parse(body);
        return callback(null, r.conditions.relative_humidity);
      }
    );
  }
};

function NidoThermostat(log, config) {
  this.log = log;
  this.requestConfig = {
    headers: {'Content-Type': 'application/json'},
    method: 'POST',
    body: { 'secret': config['secret']}
  }
  this.modeMap = config['modemapping'];

  const base = config['baseAPIUrl'];

  this.getCHCSUrl = url.parse(base + config['getCurrentHeatingCoolingState']);

  this.getTHCSUrl = url.parse(base + config['getTargetHeatingCoolingState']);
  this.setTHCSUrl = url.parse(base + config['setTargetHeatingCoolingState']);

  this.getCTUrl = url.parse(base + config['getCurrentTemperature']);

  this.getTTUrl = url.parse(base + config['getTargetTemperature']);
  this.setTTUrl = url.parse(base + config['setTargetTemperature']);

  this.getTDUUrl = url.parse(base + config['getTemperatureDisplayUnits']);
  this.setTDUUrl = url.parse(base + config['setTemperatureDisplayUnits']);

  this.getCRHUrl = url.parse(base + config['getCurrentRelativeHumidity']);

  this.errorHandler = function (that, callback, error, response) {
    that.log('STATUS: ' + response.statusCode);
    that.log(error.message);
    return callback(error);
  }

  this.issueRequest = function (that, config, callback) {
    request(
      config,
      function (error, response, body) {
        if (error) { that.errorHandler(that, callback, error, response); }
        return callback();
      }
    );
  }
};
