from nido.lib.nido import Config


class FlaskConfig(object):
    nidoConfig = Config()
    DEBUG = False
    TESTING = False
    SECRET_KEY = nidoConfig.get_config()['flask']['secret_key']
    SERVER_NAME = '0.0.0.0:443'
    GOOGLE_API_KEY = nidoConfig.get_config()['google']['api_key']
    PUBLIC_API_SECRET = nidoConfig.get_config()['flask']['public_api_secret']


class DevelopmentConfig(FlaskConfig):
    DEBUG = True
    SERVER_NAME = '127.0.0.1:80'


class ProductionConfig(FlaskConfig):
    pass
