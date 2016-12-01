import requests
import json
# Custom modules
from Adafruit_BME280 import *
from NidoConfig import NidoConfig

class Sensor():
    def __init__(self, mode=BME280_OSAMPLE_8, celsius=True):
        self.celsius = celsius
        try:
            self.sensor = BME280(mode)
        except:
            raise
        else:
            self.get_conditions()

    def get_conditions(self):
        if self.celsius:
            temp = self.sensor.read_temperature()
        else:
            temp = LocalWeather.c_to_f(self.sensor.read_temperature())
        self.conditions = {
                'temp': temp,
                'pressure_mb': self.sensor.read_pressure() / 100,
                'relative_humidity': self.sensor.read_humidity()
                }
        return self.conditions

class LocalWeather():
    def __init__(self, zipcode=None, celsius=True):
        self.zipcode = zipcode
        self.celsius = celsius
        self.api_key = NidoConfig().get_config()['wunderground']['api_key']
        try:
            self.conditions = self.get_current_conditions()
        except:
            raise

    def get_current_conditions(self):
        request_url = 'http://api.wunderground.com/api/{}/conditions/q/{}.json'.format(self.api_key, self.zipcode)
        try:
            r = requests.get(request_url)
        except:
            raise
        else:
            observation_data = r.json()['current_observation']
    
            # - Temperature in C (always convert to F)
            # - Relative humidity
            # - Location
            # - Text description of weather
            # - Current conditions weather icon
            # - Local pressure setting
    
            # Integer
            if self.celsius:
                temp = observation_data['temp_c']
            else:
                temp = LocalWeather.c_to_f(observation_data['temp_c'])
            # String
            rh = observation_data['relative_humidity']
            location = observation_data['display_location']['full']
            weather_desc = observation_data['weather']
            weather_icon = observation_data['icon_url']
            pressure = observation_data['pressure_mb']

            self.conditions = {
                    'zipcode': self.zipcode,
                    'location_name': location,
                    'temp': temp,
                    'relative_humidity': rh,
                    'local_pressure_mb': pressure,
                    'condition_desc': weather_desc,
                    'condition_icon_url': weather_icon
                    }
            return self.conditions

    @classmethod
    def c_to_f(cls, temp_c):
        return (temp_c * 1.8) + 32
