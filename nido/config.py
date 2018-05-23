from builtins import object


class FlaskConfig(object):
    DEBUG = False
    TESTING = False
    FLASK_RUN_HOST = '0.0.0.0'
    FLASK_RUN_PORT = 443
    RPC_HOST = 'localhost'
    RPC_PORT = 49152


class DevelopmentConfig(FlaskConfig):
    DEBUG = True
    FLASK_RUN_HOST = '127.0.0.1'
    FLASK_RUN_PORT = 80


class ProductionConfig(FlaskConfig):
    pass
