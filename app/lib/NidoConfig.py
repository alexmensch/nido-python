import yaml

# config.yaml sections and values available
#############
# GPIO
#   heat_pin
#   cool_pin
# behavior
#   hysteresis
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
# daemon
#   pid_file
#   log_file
#   work_dir
#   poll_interval
#############

class NidoConfig():
    def __init__(self):
        self._CONFIG = '/home/pi/nido/app/cfg/config.yaml'
        return
    
    def get_config(self):
        with open(self._CONFIG, 'r') as f:
            return yaml.load(f)

    def set_config(self, config):
        with open(self._CONFIG, 'w') as f:
            yaml.dump(config, f)
        return
