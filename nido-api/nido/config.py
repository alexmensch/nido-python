from builtins import object

import os


class FlaskConfig(object):
    ENV = "production"
    DEBUG = False
    TESTING = False
    RPC_HOST = os.environ["NIDOD_RPC_HOST"]
    RPC_PORT = int(os.environ["NIDOD_RPC_PORT"])


class DevelopmentConfig(FlaskConfig):
    ENV = "development"
    DEBUG = True


class ProductionConfig(FlaskConfig):
    pass
