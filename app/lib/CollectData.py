import requests
import json
import time
from Adafruit_BME280 import *
from NidoConfig import NidoConfig

class Sensor():
    def __init__(self, mode=BME280_OSAMPLE_8):
        try:
            self.sensor = BME280(mode)
        except:
            raise

    def get_conditions(self):
        # Initialize response dict
        resp = {}

        # Get sensor data
        try:
            conditions = {
                'temp_c': self.sensor.read_temperature(),
                'pressure_mb': self.sensor.read_pressure() / 100,
                'relative_humidity': self.sensor.read_humidity()
                }
        except Exception as e:
            resp['error'] = 'Exception getting sensor data: {} {}'.format(type(e), str(e))
        else:
            resp['conditions'] = conditions
        
        return resp

class LocalWeather():
    def __init__(self, zipcode=None, location=None):
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
        self._CACHE_EXPIRY = 60
        self.api_key = NidoConfig().get_config()['wunderground']['api_key']

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

    def get_conditions(self):
        # Initialize response dict
        resp = {}
        # How long since last retrieval?
        interval = int(time.time()) - self.last_req
        # System clock must have changed. Make cache stale.
        if interval < 0:
            interval = self._CACHE_EXPIRY
        # We've never made a request.
        if self.last_req == 0:
            interval = -1

        # If we made a request within caching period and have a cached result, use that instead
        if self.conditions and (interval < self._CACHE_EXPIRY) and (interval >= 0):
            resp['conditions'] = self.conditions
            resp['retrieval_age'] = interval
            return resp

        # Determine location query type
        # API documentation here: http://api.wunderground.com/weather/api/d/docs?d=data/index
        if (self.location is None) and (self.zipcode is None):
            query = 'autoip'
        elif self.location:
            query = ','.join(map(str, self.location))
        elif self.zipcode:
            query = self.zipcode

        # Set up Wunderground API request
        request_url = 'http://api.wunderground.com/api/{}/conditions/q/{}.json'.format(self.api_key, query)
        try:
            r = requests.get(request_url)
        except Exception as e:
            # Making the request failed
            resp['error'] = 'Error retrieving local weather: {}'.format(e)
            # If we have any cached conditions (regardless of age), return them
            if self.conditions:
                resp['conditions'] = self.conditions
                resp['retrieval_age'] = interval
        else:
            # Request was successful, parse response JSON
            r_json = r.json()
            try:
                observation_data = r_json['current_observation']
            except KeyError:
                # 'current_observation' data is missing, look for error description in response
                try:
                    api_error = r_json['response']['error']
                except KeyError:
                    # Error description was missing, return full response data instead
                    resp['error'] = 'Unknown Wunderground API error. Response data: ' + str(r_json)
                    # If we have any cached conditions (regardless of age), return them
                    if self.conditions:
                        resp['conditions'] = self.conditions
                        resp['retrieval_age'] = interval
                else:
                    # Return error type and description from Wunderground API
                    resp['error'] = 'Wunderground API error (' + api_error['type'] + '): ' + api_error['description']
                    # If we have any cached conditions (regardless of age), return them
                    if self.conditions:
                        resp['conditions'] = self.conditions
                        resp['retrieval_age'] = interval
            else:
                # 'current_observation' data was available, parse conditions
                try:
                    self.conditions = {
                            'zipcode': observation_data['display_location']['zip'],
                            'location': {
                                'full': observation_data['display_location']['full'],
                                'city': observation_data['display_location']['city'],
                                'state': observation_data['display_location']['state'],
                                'country': observation_data['display_location']['country'],
                                'coordinates': {
                                    'latitude': observation_data['display_location']['latitude'],
                                    'longitude': observation_data['display_location']['longitude']
                                    },
                                },
                            'temp_c': "{}".format(observation_data['temp_c']),
                            'relative_humidity': observation_data['relative_humidity'],
                            'pressure_mb': observation_data['pressure_mb'],
                            'condition': {
                                'description': observation_data['weather'],
                                'icon_url': observation_data['icon_url']
                                }
                            }
                except KeyError as e:
                    # Something changed in the response format, generate an error
                    resp['error'] = 'Error parsing Wunderground API data: {}' + str(e)
                else:
                    # Otherwise, if we successfully got here, everything actually worked!
                    resp['conditions'] = self.conditions
                    # Reset retrieval time and update response
                    self.last_req = int(time.time())
                    resp['retrieval_age'] = 0
        
        return resp
