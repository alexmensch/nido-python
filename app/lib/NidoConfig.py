import yaml
from NidoConstants import Mode, FormTypes

class NidoConfig():
    def __init__(self):
        self._CONFIG = '/home/pi/nido/app/cfg/config.yaml'
        self._SCHEMA_VERSION = '1.0'
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
                'config': {
                    'location': {
                        'form_data': (FormTypes.text.name, None),
                        'label': 'Location',
                        'required': False
                        },
                    'celsius': {
                        'required': False,
                        'default': True
                        },
                    'modes_available': {
                        'form_data': (FormTypes.checkbox.name, [ [ Mode.Heat.name, True ], [ Mode.Cool.name, False ] ]),
                        'label': 'Available modes',
                        'required': False,
                        'default': [ Mode.Heat.name ]
                        },
                    'set_temperature': {
                        'required': False,
                        'default': 21
                        },
                    'modes': {
                        'required': False,
                        'default': [ Mode.Off.name, Mode.Heat.name ]
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
                        },
                    'poll_interval': {
                        'required': False,
                        'default': 300
                        }
                    }
                }
        return
    
    def get_config(self):
        with open(self._CONFIG, 'r') as f:
            return yaml.load(f)

    def set_config(self, config):
        with open(self._CONFIG, 'w') as f:
            yaml.dump(config, f, default_flow_style=False, indent=4)
        return

    def get_schema(self, section):
        return self._SCHEMA[section]

    def get_version(self):
        return self._SCHEMA_VERSION

    def validate(self):
        config = self.get_config()

        # Iterate through schema and check required flag against loaded config
        for section in self._SCHEMA:
            for setting in self._SCHEMA[section]:
                if self._SCHEMA[section][setting]['required'] == True:
                    if section not in config:
                        return False
                    elif setting not in config[section]:
                        return False
                # If setting is not required, check if a default value exists
                #   and set it if not set in the config
                elif 'default' in self._SCHEMA[section][setting]:
                    if section not in config:
                        default_setting = {
                                section: {
                                    setting: self._SCHEMA[section][setting]['default']
                                    }
                                }
                        config.update(default_setting)
                    elif setting not in config[section]:
                        config[section][setting] = self._SCHEMA[section][setting]['default']

        # Write any changes to config back to disk and return True since we found all required settings
        self.set_config(config)
        return True

    @staticmethod
    def list_modes(modes_available):
        modes = [ Mode.Off.name ]
        for mode in modes_available:
            if mode[1] is True:
                modes.append(mode[0])
        if len(modes) == 3:
            modes.append(Mode.Heat_Cool.name)
        return modes
