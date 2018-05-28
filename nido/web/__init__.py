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

from __future__ import print_function
from builtins import str
from builtins import object
from builtins import map

import requests
from requests import RequestException
import re
import time
from flask import current_app

from nidod.lib.hardware import Config, ConfigError
from nidod.lib.client.scheduler import SchedulerClient, SchedulerClientError


class LocalWeather(object):
    def __init__(self, api_key, zipcode=None, location=None):
        self._api_key = api_key
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
                self._api_key, 'conditions/forecast/astronomy',
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


def set_config_helper(resp, cfg=None, mode=None, temp_scale=None):
    _CONFIG = Config()
    sc = SchedulerClient(current_app.config['RPC_HOST'],
                         current_app.config['RPC_PORT'])
    if mode:
        if _CONFIG.set_mode(mode):
            resp.data['message'] = 'Mode updated successfully.'
        else:
            resp.data['error'] = 'Invalid mode.'
            resp.status = 400
    elif temp_scale:
        if _CONFIG.set_temp(temp_scale[0], temp_scale[1]):
            resp.data['message'] = 'Temperature updated successfully.'
        else:
            resp.data['error'] = 'Invalid temperature.'
            resp.status = 400
    elif cfg:
        if _CONFIG.update_config(cfg):
            resp.data['message'] = 'Configuration updated successfully.'
        else:
            resp.data['error'] = 'Invalid configuration setting(s).'
            resp.status = 400
    else:
        raise ConfigError('No configuration setting specified.')

    resp.data['config'] = _CONFIG.get_config()['config']

    # Send signal to daemon, if running, to trigger update
    try:
        sc.wakeup()
    except SchedulerClientError as e:
        resp.data['warning'] = 'Error signalling daemon: {}'.format(e)
    return resp


# Helper function to validate JSON in requests
# A list of tuples is passed in of the form ( 'name', type )
# Where:
#        'name' is the key we expect in the dict
#        type is a type we can compare the corresponding value to
#        using isinstance()
###
# TODO: Improve validation
#       eg. location should be a list of only two numbers
#       eg. modes_available be a list of lists, each with only
#           two values
def validate_json_req(req_data, valid):
    # Make sure we have JSON in the body first
    if req_data is None or req_data == {}:
        return False

    # Request data can't have more entries than the validation set
    if len(valid) < len(req_data):
        print('Bad length')
        return False

    # Check that each element in the request data is valid
    for setting in req_data:
        if setting not in valid:
            print('Setting name is not in valid dict')
            return False
        elif not isinstance(req_data[setting], valid[setting]):
            print('Setting value is not instance of valid type')
            print(
                'setting: {}, type: {}'
                .format(req_data[setting], type(req_data[setting]))
            )
            print('valid type: {}'.format(valid[setting]))
            return False

    # No tests failed
    return True
