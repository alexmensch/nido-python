#   Nido, a Raspberry Pi-based home thermostat.
#
#   Copyright (C) 2016 Alex Marshall
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program.
#   If not, see <http://www.gnu.org/licenses/>.

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function
from future import standard_library
standard_library.install_aliases()
from builtins import *
from builtins import map
from builtins import str
from builtins import object

import requests
from requests import RequestException
import time
import yaml
import os
import re
import logging
from enum import Enum

if 'NIDO_TESTING' in os.environ:
    from .testing import FakeGPIO, FakeSensor as BME280
    GPIO = FakeGPIO(os.environ['NIDO_TESTING_GPIO'])
    BME280_OSAMPLE_8 = None
else:
    import RPi.GPIO as GPIO
    from .Adafruit_BME280 import BME280, BME280_OSAMPLE_8

_NIDO_BASE = os.environ['NIDO_BASE']

# Enums:
#   Mode
#   Status
#   FormTypes
# Weather data:
#   LocalWeather
# Hardware data:
#   Sensor
# Hardware control:
#   ControllerError
#   Controller
# Configuration:
#   ConfigError
#   Config


class Mode(Enum):
    Off = 0
    Heat = 1
    Cool = 2
    Heat_Cool = 3


class Status(Enum):
    Off = 0
    Heating = 1
    Cooling = 2


class FormTypes(Enum):
    text = 0
    password = 1
    checkbox = 2
    radio = 3
    select = 4
    textarea = 5


class Sensor(object):
    def __init__(self, mode=BME280_OSAMPLE_8):
        self.sensor = BME280(mode)
        self._l = logging.getLogger(__name__)
        return None

    def get_conditions(self):
        # Initialize response dict
        resp = {}

        # Get sensor data
        try:
            temp_c = self.sensor.read_temperature()
            pressure_mb = self.sensor.read_pressure() / 100
            relative_humidity = self.sensor.read_humidity()
            self._l.debug(
                'Sensor data: T = {}C | P = {} | RH = {}'
                .format(temp_c, pressure_mb, relative_humidity)
            )
        except Exception as e:
            resp['error'] = (
                'Exception getting sensor data: {} {}'.format(type(e), str(e))
            )
        else:
            conditions = {
                'temp_c': temp_c,
                'pressure_mb': pressure_mb,
                'relative_humidity': relative_humidity
            }
            resp['conditions'] = conditions

        return resp


class LocalWeather(object):
    def __init__(self, zipcode=None, location=None):
        self._l = logging.getLogger(__name__)
        if zipcode:
            self.set_zipcode(zipcode)
        else:
            self.zipcode = None
        if location:
            self.set_location(location)
        else:
            self.location = None
        self.conditions = None
        # Unix time of last request to implement basic caching
        self.last_req = 0
        # Cache expiry period in seconds
        # 900 == 15 minutes
        self._CACHE_EXPIRY = 900
        self.api_key = Config().get_config()['wunderground']['api_key']

    def set_zipcode(self, zipcode):
        if not isinstance(zipcode, int):
            raise TypeError
        self.zipcode = zipcode
        self.conditions = None
        return

    def set_location(self, location):
        if not isinstance(location, tuple):
            raise TypeError
        self.location = location
        self.conditions = None
        return

    def _wunderground_req(self, request_url):
        try:
            r = requests.get(request_url)
        except RequestException as e:
            # Making the request failed
            resp = {}
            resp['error'] = 'Error retrieving local weather: {}'.format(e)
            return resp
        else:
            return r

    def _wunderground_parse_result(self, r):
        resp = {}
        r_json = r.json()
        try:
            current_observation = r_json['current_observation']
            forecast = r_json['forecast']['simpleforecast']['forecastday']
            sun_phase = r_json['sun_phase']
        except KeyError:
            try:
                api_error = r_json['response']['error']
            except KeyError:
                resp['error'] = (
                    'Unknown Wunderground API error. Response data: '
                    + str(r_json)
                )
            else:
                if 'description' in api_error:
                    resp['error'] = (
                        'Wunderground API error ({}): {}'
                        .format(api_error['type'], api_error['description'])
                    )
                else:
                    resp['error'] = (
                        'Wunderground API error ({})'.format(api_error['type'])
                    )
        else:
            try:
                # Remove '%' and format relatively humidity as a number
                rh = re.sub('[^0-9]', '',
                            current_observation['relative_humidity'])
                rh = int(float(rh))
                # Get shortest term high/low forecast
                for period in forecast:
                    if period['period'] == 1:
                        fcast_high = float(period['high']['celsius'])
                        fcast_low = float(period['low']['celsius'])

                display_location = current_observation['display_location']
                sunrise = sun_phase['sunrise']
                sunset = sun_phase['sunset']
                self.conditions = {
                    'location': {
                        'full': display_location['full'],
                        'city': display_location['city'],
                        'state': display_location['state'],
                        'zipcode': display_location['zip'],
                        'country': display_location['country'],
                        'coordinates': {
                            'latitude': display_location['latitude'],
                            'longitude': display_location['longitude']
                        }
                    },
                    'temp_c': current_observation['temp_c'],
                    'relative_humidity': rh,
                    'pressure_mb': current_observation['pressure_mb'],
                    'condition': {
                        'description': current_observation['weather'],
                        'icon_url': current_observation['icon_url']
                    },
                    'forecast': {
                        'high': fcast_high,
                        'low': fcast_low
                    },
                    'solar': {
                        'sunrise': int(sunrise['hour'] + sunrise['minute']),
                        'sunset': int(sunset['hour'] + sunset['minute'])
                    }
                }
                # Convert icon URL to HTTPS
                icon_url = re.sub('(http)', 'https',
                                  current_observation['icon_url'], count=1)
                self.conditions['condition']['icon_url'] = icon_url
            except KeyError as e:
                # Something changed in the response format, generate an error
                resp['error'] = (
                    'Error parsing Wunderground API data: {}'.format(str(e))
                )
            else:
                # Reset retrieval time
                self.last_req = int(time.time())
                self._interval = 0
        finally:
            return resp

    def get_conditions(self):
        # Initialize response dict
        resp = {}
        # How long since last retrieval?
        self._interval = int(time.time()) - self.last_req
        # System clock must have changed. Make cache stale.
        if self._interval < 0:
            self._interval = self._CACHE_EXPIRY
        # We've never made a request.
        if self.last_req == 0:
            self._interval = -1

        # If we made a request within caching period and have a cached
        # result, use that instead
        if (self.conditions and (self._interval < self._CACHE_EXPIRY)
                and (self._interval >= 0)):
            resp['weather'] = self.conditions
            resp['retrieval_age'] = self._interval
            return resp

        # Determine location query type
        # API documentation here:
        # http://api.wunderground.com/weather/api/d/docs?d=data/index
        # Prefer lat,long over zipcode
        if (self.location is None) and (self.zipcode is None):
            query = 'autoip'
        elif self.location:
            query = ','.join(map(str, self.location))
        elif self.zipcode:
            query = self.zipcode

        # Get Wunderground weather conditions
        request_url = (
            'https://api.wunderground.com/api/{}/{}/q/{}.json'
            .format(
                self.api_key, 'conditions/forecast/astronomy',
                query
            )
        )
        api_response = self._wunderground_req(request_url)

        if isinstance(api_response, requests.Response):
            resp.update(self._wunderground_parse_result(api_response))
        else:
            resp.update(api_response)

        if self.conditions:
            resp['weather'] = self.conditions
            resp['retrieval_age'] = self._interval

        return resp


class ControllerError(Exception):
    """Exception class for errors generated by the controller"""

    def __init__(self, msg):
        self.msg = msg
        return

    def __str__(self):
        return repr(self.msg)


class Controller(object):
    """This is the controller code that determines whether the
    heating / cooling system should be enabled based on the thermostat
    set point."""

    def __init__(self):
        self._l = logging.getLogger(__name__)
        try:
            self.cfg = Config()
            config = self.cfg.get_config()
        except IOError as e:
            raise ControllerError(
                'Error getting configuration: {}'.format(str(e))
            )
        else:
            self._HEATING = config['GPIO']['heat_pin']
            self._COOLING = config['GPIO']['cool_pin']

        # Set up the GPIO pins
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self._HEATING, GPIO.OUT)
        GPIO.setup(self._COOLING, GPIO.OUT)
        self._l.debug(
            'GPIO pins configured: heat = {} | cool = {}'
            .format(self._HEATING, self._COOLING)
        )

        return

    def get_status(self):
        if (GPIO.input(self._HEATING) and GPIO.input(self._COOLING)):
            self._l.error('** Both heating and cooling pins enabled. **')
            self.shutdown()
            raise ControllerError(
                'Both heating and cooling pins were enabled. '
                'Both pins disabled as a precaution.'
            )
        elif GPIO.input(self._HEATING):
            self._l.debug('Get status: {}'.format(Status.Heating.name))
            return Status.Heating.value
        elif GPIO.input(self._COOLING):
            self._l.debug('Get state: {}'.format(Status.Cooling.name))
            return Status.Cooling.value
        else:
            self._l.debug('Get state: {}'.format(Status.Off.name))
            return Status.Off.value

    def _enable_heating(self, status, temp, set_temp, hysteresis):
        if (temp + hysteresis) < set_temp:
            GPIO.output(self._HEATING, True)
            GPIO.output(self._COOLING, False)
            self._l.debug(
                'Enabled HEAT: {} < {}'.format(temp + hysteresis, set_temp)
            )
        elif (temp < set_temp) and (status is Status.Heating):
            GPIO.output(self._HEATING, True)
            GPIO.output(self._COOLING, False)
            self._l.debug(
                'Enabled HEAT: {} < {} and status = Heating'
                .format(temp, set_temp)
            )
        return

    def _enable_cooling(self, status, temp, set_temp, hysteresis):
        if (temp + hysteresis) > set_temp:
            GPIO.output(self._HEATING, False)
            GPIO.output(self._COOLING, True)
        elif (temp > set_temp) and (status is Status.Cooling):
            GPIO.output(self._HEATING, False)
            GPIO.output(self._COOLING, True)
        return

    def shutdown(self):
        GPIO.output(self._HEATING, False)
        GPIO.output(self._COOLING, False)
        self._l.debug('Shut down GPIO pins.')
        return

    def update(self):
        config = self.cfg.get_config()
        try:
            mode = config['config']['mode_set']
            status = self.get_status()
            temp = Sensor().get_conditions()['conditions']['temp_c']
            set_temp = float(config['config']['set_temperature'])
            hysteresis = config['behavior']['hysteresis']
        except KeyError as e:
            self.shutdown()
            raise ControllerError('Error reading Nido configuration: {}'
                                  .format(e))
        except ControllerError:
            self.shutdown()
            raise

        if mode == Mode.Off.name:
            self._l.debug('Mode = Off | Set temp {}C'.format(set_temp))
            self.shutdown()
        elif mode == Mode.Heat.name:
            self._l.debug('Mode = Heat | Set temp {}C'.format(set_temp))
            if temp < set_temp:
                self._enable_heating(status, temp, set_temp, hysteresis)
            else:
                self.shutdown()
        else:
            # Additional modes can be enabled in future, eg. Mode.Cool,
            # Mode.Heat_Cool
            self.shutdown()

        return

    def daemon_running(self):
        pid_file = self.cfg.get_config()['daemon']['pid_file']
        return os.path.isfile(pid_file)


class ConfigError(Exception):
    """Exception class for errors generated by the Config class"""

    def __init__(self, msg):
        self.msg = msg
        return

    def __str__(self):
        return repr(self.msg)


class Config(object):
    def __init__(self):
        self._CONFIG = '{}/nido/cfg/config.yaml'.format(_NIDO_BASE)
        self._SCHEMA_VERSION = '1.3'
        self._SCHEMA = {
            'GPIO': {
                'heat_pin': {
                    'required': True
                },
                'cool_pin': {
                    'required': True
                },
            },
            'behavior': {
                'hysteresis': {
                    'required': False,
                    'default': 0.6
                }
            },
            'flask': {
                'port': {
                    'required': True
                },
                'debug': {
                    'required': False,
                    'default': False
                },
                'secret_key': {
                    'required': True
                },
                'public_api_secret': {
                    'required': True
                },
                'username': {
                    'required': True
                },
                'password': {
                    'required': True
                }
            },
            'wunderground': {
                'api_key': {
                    'required': True
                }
            },
            'google': {
                'api_key': {
                    'required': True
                }
            },
            'config': {
                'location': {
                    'required': False
                },
                'location_label': {
                    'required': False
                },
                'celsius': {
                    'required': False,
                    'default': True
                },
                'modes_available': {
                    'required': False,
                    'default': [[Mode.Heat.name, True],
                                [Mode.Cool.name, False]]
                },
                'set_temperature': {
                    'required': False,
                    'default': 21
                },
                'modes': {
                    'required': False,
                    'default': [Mode.Off.name, Mode.Heat.name]
                },
                'mode_set': {
                    'required': False,
                    'default': Mode.Off.name
                }
            },
            'daemon': {
                'pid_file': {
                    'required': True
                },
                'log_file': {
                    'required': True
                },
                'work_dir': {
                    'required': True
                }
            },
            'schedule': {
                'poll_interval': {
                    'required': False,
                    'default': 300
                },
                'db': {
                    'required': True
                },
                'rpc_host': {
                    'required': False,
                    'default': 'localhost'
                },
                'rpc_port': {
                    'required': False,
                    'default': 49152
                }
            }
        }
        if self._is_valid():
            return
        else:
            raise ConfigError(
                'Error: incomplete configuration, please verify '
                'config.yaml settings.'
            )

    def get_config(self):
        with open(self._CONFIG, 'r') as f:
            return yaml.load(f)

    def get_schema(self, section):
        return self._SCHEMA[section]

    def get_version(self):
        return self._SCHEMA_VERSION

    def update_config(self, new_cfg, cfg=None):
        if cfg is None:
            cfg = self.get_config()
        for setting in new_cfg:
            if setting == 'modes_available':
                cfg['config']['modes'] = self.list_modes(new_cfg[setting])
            cfg['config'][setting] = new_cfg[setting]

        return self._is_valid(config=cfg)

    def set_temp(self, temp, scale, cfg=None):
        if cfg is None:
            cfg = self.get_config()

        new_cfg = cfg['config']
        scale = scale.upper()

        if scale == 'C':
            new_cfg['set_temperature'] = temp
        elif scale == 'F':
            # The following conversion duplicates the logic in nido.js
            celsius_temp = (temp - 32) * 5 / 9
            celsius_temp = round(celsius_temp * 10) / 10
            celsius_temp = float("{0:.1f}".format(celsius_temp))
            new_cfg['set_temperature'] = celsius_temp

        return self.update_config(new_cfg, cfg=cfg)

    def set_mode(self, mode, cfg=None):
        if cfg is None:
            cfg = self.get_config()

        new_cfg = cfg['config']
        modes = self.list_modes(cfg['config']['modes_available'])

        for m in modes:
            if m.upper() == mode.upper():
                new_cfg['mode_set'] = m
                return self.update_config(new_cfg, cfg=cfg)

        return False

    def _set_config(self, config):
        with open(self._CONFIG, 'w') as f:
            yaml.dump(config, f, default_flow_style=False, indent=4)
        return

    def _is_valid(self, config=None, set_defaults=True, update=True):
        if config is None:
            config = self.get_config()

        # Iterate through schema and check required flag against
        # loaded config
        schema = self._SCHEMA
        for section in schema:
            for setting in schema[section]:
                if schema[section][setting]['required'] is True:
                    if section not in config:
                        return False
                    elif setting not in config[section]:
                        return False
                # If setting is not required, check if a default value
                #   exists and set it if not set in the config.
                elif (set_defaults and 'default'
                      in schema[section][setting]):
                    if section not in config:
                        default_setting = {
                            section: {
                                setting: schema[section][setting]['default']
                            }
                        }
                        config.update(default_setting)
                    elif setting not in config[section]:
                        config[section][setting] = (
                            schema[section][setting]['default']
                        )

        if update:
            self._set_config(config)
        return True

    @staticmethod
    def list_modes(modes_available):
        modes = [Mode.Off.name]
        heat = False
        cool = False

        for mode in modes_available:
            if mode[1] is True:
                if mode[0] == Mode.Heat.name:
                    heat = True
                elif mode[0] == Mode.Cool.name:
                    cool = True
                modes.append(mode[0])
        if heat and cool:
            modes.append(Mode.Heat_Cool.name)
        return modes
