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
    me.log(config.url.href);

    request(
      config, 
      function (error, response, body) {
        if (error) { me.errorHandler(me, callback, error, response); }
        else { return callback(null, response.body.state.value); }
      }
    );
  },

  getTargetHeatingCoolingState: function (callback) {
    const me = this;
    const config = {
      ...me.requestConfig,
      ...{ url: me.getTHCSUrl }
    };
    me.log(config.url.href);

    request(
      config,
      function (error, response, body) {
        if (error) { me.errorHandler(me, callback, error, response); }
        else { return callback(null, response.body.mode.value); }
      }
    );
  },

  setTargetHeatingCoolingState: function (set, callback) {
    const me = this;
    const setVal = me.modeMap[set]
    const setUrl = url.parse(me.setTHCSUrl.href + setVal);
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
    me.log(config.url.href);

    request(
      config,
      function (error, response, body) {
        if (error) { me.errorHandler(me, callback, error, response); }
        else { return callback(null, response.body.conditions.temp_c); }
      }
    );
  },

  getTargetTemperature: function (callback) {
    const me = this;
    const config = {
      ...me.requestConfig,
      ...{ url: me.getTTUrl }
    };
    me.log(config.url.href);

    request(
      config,
      function (error, response, body) {
        if (error) { me.errorHandler(me, callback, error, response); }
        else { return callback(null, response.body.temp.celsius); }
      }
    );
  },

  setTargetTemperature: function (set, callback) {
    const me = this;
    const setUrl = url.parse(me.setTTUrl.href + set + '/C');
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
    me.log(config.url.href);

    request(
      config,
      function (error, response, body) {
        if (error) { me.errorHandler(me, callback, error, response); }        
        else { return callback(null, response.body.celsius ? 1 : 0); }
      }
    );
  },

  setTemperatureDisplayUnits: function (set, callback) {
    const me = this;
    const setVal = set ? 'F' : 'C';
    const setUrl = url.parse(me.setTDUUrl.href + setVal);
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
    me.log(config.url.href);

    request(
      config,
      function (error, response, body) {
        if (error) { me.errorHandler(me, callback, error, response); }
        else { return callback(null, response.body.conditions.relative_humidity); }
      }
    );
  }
};

function NidoThermostat(log, config) {
  this.log = log;
  this.requestConfig = {
    method: 'POST',
    json: true,
    body: { 'secret': config['secret'] }
  }
  this.modeMap = config['modemapping'];

  const base = config['baseAPIUrl'];

  this.getCHCSUrl = url.parse(base + config['getCHCSUrl']);

  this.getTHCSUrl = url.parse(base + config['getTHCSUrl']);
  this.setTHCSUrl = url.parse(base + config['setTHCSUrl']);

  this.getCTUrl = url.parse(base + config['getCTUrl']);

  this.getTTUrl = url.parse(base + config['getTTUrl']);
  this.setTTUrl = url.parse(base + config['setTTUrl']);

  this.getTDUUrl = url.parse(base + config['getTDUUrl']);
  this.setTDUUrl = url.parse(base + config['setTDUUrl']);

  this.getCRHUrl = url.parse(base + config['getCRHUrl']);

  this.errorHandler = function (that, callback, error, response) {
    that.log(error.message);
    if (response) {
      that.log('STATUS: ' + response.statusCode);
    }
    return callback(error);
  }

  this.issueRequest = function (that, config, callback) {
    request(
      config,
      function (error, response, body) {
        if (error) { that.errorHandler(that, callback, error, response); }
        else { return callback(); }
      }
    );
  }
};
