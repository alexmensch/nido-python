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
    DB_PATH = '{}/nidod/db/nido.db'.format(os.environ['NIDO_BASE'])
    # Convert to env variables
    NIDOD_RPC_HOST = ''  # This is also referenced in nido/config.py
    NIDOD_RPC_PORT = ''  # This is also referenced in nido/config.py


class DaemonConfig(object):
    # Convert to env variables
    NIDOD_PID_FILE = ''
    NIDOD_WORK_DIR = ''
    NIDOD_LOG_FILE = ''


class HardwareConfig(object):
    GPIO_COOL_PIN = 20
    GPIO_HEAT_PIN = 26
    HYSTERESIS = 0.6
    MODES = [Mode.Off.name, Mode.Heat.name]
    # Need modes_available method, copy in from Config object
