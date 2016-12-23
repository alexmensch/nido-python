from enum import Enum

class Mode(Enum):
    off = 0
    heat = 1
    cool = 2
    heat_cool = 3

class Status(Enum):
    off = 0
    heating = 1
    cooling = 2

# No longer used, might be useful for UI definitions instead

# _MODE_NAME = {
#        Mode.off: 'Off',
#        Mode.heat: 'Heat',
#        Mode.cool: 'Cool',
#        Mode.heat_cool: 'Heat/Cool'
#        }

#_STATUS_NAME = {
#        Status.off: 'Off',
#        Status.heating: 'Heating',
#        Status.cooling: 'Cooling'
#        }
