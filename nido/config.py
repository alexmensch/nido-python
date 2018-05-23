from builtins import object
from nido.lib.nido import Config


class FlaskConfig(object):
    nidoConfig = Config()
    DEBUG = False
    TESTING = False
    SECRET_KEY = nidoConfig.get_config()['flask']['secret_key']
    HOST = '0.0.0.0'
    PORT = 443
    GOOGLE_API_KEY = nidoConfig.get_config()['google']['api_key']
    PUBLIC_API_SECRET = nidoConfig.get_config()['flask']['public_api_secret']


class DevelopmentConfig(FlaskConfig):
    DEBUG = True
    FLASK_RUN_HOST = '127.0.0.1'
    FLASK_RUN_PORT = 80


class ProductionConfig(FlaskConfig):
    pass
