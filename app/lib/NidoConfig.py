import yaml
from NidoConstants import Mode, FormTypes

class NidoConfig():
    def __init__(self):
        self._CONFIG = '/home/pi/nido/app/cfg/config.yaml'
        self._SCHEMA_VERSION = '1.0.0'
        self._SCHEMA = {
                'GPIO': {
                    'heat_pin': {
                        'form_data': (FormTypes.text.name, None),
                        'label': 'Heating pin'
                        },
                    'cool_pin': {
                        'form_data': (FormTypes.text.name, None),
                        'label': 'Cooling pin'
                        },
                    },
                'behavior': {
                    'hysteresis': {
                        'form_data': (FormTypes.text.name, 0.6),
                        'label': 'Hysteresis'
                        }
                    },
                'flask': {
                    'port': {
                        'form_data': (FormTypes.text.name, 8080),
                        'label': 'Port'
                        },
                    'debug': {
                        'form_data': (FormTypes.radio.name, [ False, True ]),
                        'label': 'Debug'
                        },
                    'secret-key': {
                        'form_data': (FormTypes.text.name, None),
                        'label': 'Secret key'
                        },
                    'username': {
                        'form_data': (FormTypes.text.name, None),
                        'label': 'Username'
                        },
                    'password': {
                        'form_data': (FormTypes.password.name, None),
                        'label': 'Password'
                        }
                    },
                'wunderground': {
                    'api_key': {
                        'form_data': (FormTypes.text.name, None),
                        'label': 'API key'
                        }
                    },
                'config': {
                    'location': {
                        'form_data': (FormTypes.text.name, '0.0,0.0'),
                        'label': 'Location'
                        },
                    'location_name': {
                        'form_data': (FormTypes.text.name, None),
                        'label': 'Location name'
                        },
                    'nido_location': {
                        'form_data': (FormTypes.text.name, 'My Home'),
                        'label': 'Nido location'
                        },
                    'celsius': {
                        'form_data': (FormTypes.radio.name, [ 'Celsius', 'Fahrenheit' ]),
                        'label': 'Temperature'
                        },
                    'mode': {
                        'form_data': (FormTypes.select.name, [ Mode.Off.name, Mode.Heat.name, Mode.Cool.name, Mode.Heat_Cool.name ]),
                        'label': 'Mode'
                        },
                    'set_temperature': {
                        'form_data': (FormTypes.text.name, 21),
                        'label': 'Set point'
                        }
                    },
                'user': {
                    'name_first': {
                        'form_data': (FormTypes.text.name, None),
                        'label': 'First name'
                        },
                    'name_last': {
                        'form_data': (FormTypes.text.name, None),
                        'label': 'Last name'
                        },
                    'email': {
                        'form_data': (FormTypes.text.name, None),
                        'label': 'Email'
                        }
                    },
                'daemon': {
                    'pid_file': {
                        'form_data': (FormTypes.text.name, '/tmp/nidod.pid'),
                        'label': 'PID file'
                        },
                    'log_file': {
                        'form_data': (FormTypes.text.name, '/var/log/nidod.log'),
                        'label': 'Log file'
                        },
                    'work_dir': {
                        'form_data': (FormTypes.text.name, '/tmp'),
                        'label': 'Working directory'
                        },
                    'poll_interval': {
                        'form_data': (FormTypes.text.name, 300),
                        'label': 'Poll interval'
                        }
                    }
                }
        return
    
    def get_config(self):
        with open(self._CONFIG, 'r') as f:
            return yaml.load(f)

    def set_config(self, config):
        with open(self._CONFIG, 'w') as f:
            yaml.dump(config, f)
        return

    def get_schema(self, section):
        return self._SCHEMA[section]

    def get_version(self):
        return self._SCHEMA_VERSION
