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

class FormTypes(Enum):
    text = 0
    password = 1
    checkbox = 2
    radio = 3
    select = 4
    textarea = 5
