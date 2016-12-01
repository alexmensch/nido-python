import yaml

# config.yaml sections and values available
#############
# GPIO
#   heat_pin
#   cool_pin
# behavior
#   hysteresis_c
#   hysteresis_f
# flask
#   port
#   debug
#   secret_key
#   username
#   password
# wunderground
#   api_key
# settings
#   location: [latitude, longitude]
#   location_name
#   nido_location
#   celsius
#   mode
#   set_temperature
# user
#   name_first
#   name_last
#   email

class NidoConfig():
    def __init__(self):
        try:
            self.config_file = file('/home/pi/nido/dev/cfg/config.yaml', 'r+')
        except:
            raise
        else:
            self.config = yaml.load(self.config_file)
            return
    
    def get_config(self):
        return self.config

    def set_config(self, config):
        self.config = config
        try:
            yaml.dump(self.config, self.config_file)
        except:
            raise
        else:
            return
