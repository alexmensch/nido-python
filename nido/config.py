from builtins import object


class FlaskConfig(object):
    ENV = 'production'
    DEBUG = False
    TESTING = False

    RPC_HOST = 'localhost'
    RPC_PORT = 49152


class DevelopmentConfig(FlaskConfig):
    ENV = 'development'
    DEBUG = True


class ProductionConfig(FlaskConfig):
    pass
