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
