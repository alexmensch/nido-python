import yaml

class NidoConfig():
    def __init__(self):
        try:
            self.config_file = file('/home/pi/nido/dev/cfg/config.yaml', 'r')
        except:
            raise
        else:
            self.config = yaml.load(self.config_file)
    
    def get_config(self):
        return self.config
