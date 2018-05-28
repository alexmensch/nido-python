from builtins import object

import os

from enum import Enum


class Mode(Enum):
    Off = 0
    Heat = 1
    Cool = 2
    Heat_Cool = 3


class Status(Enum):
    Off = 0
    Heating = 1
    Cooling = 2


class SchedulerConfig(object):
    POLL_INTERVAL = 300


class DaemonConfig(object):
    DB_PATH = '{}/nidod/db/nido.sqlite'.format(os.environ['NIDO_BASE'])
    PID_FILE = os.environ['NIDOD_PID_FILE']


class HardwareConfig(object):
    GPIO_COOL_PIN = 20
    GPIO_HEAT_PIN = 26
    HYSTERESIS = 0.6
    MODES = [Mode.Off.name, Mode.Heat.name]
    # Need modes_available method, copy in from Config object
