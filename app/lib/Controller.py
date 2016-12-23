from enum import Enum
import RPi.GPIO as GPIO
from CollectData import Sensor
from NidoConstants import Mode, Status
from NidoConfig import NidoConfig

# This is the controller code that determines whether the heating / cooling system
# should be enabled based on the thermostat set point.
#
# TODO: Turn this into a Class instead :-)
# TODO: Record start/stop times for all heating/cooling events

# Configuration
cfg = NidoConfig().get_config()

# GPIO pin assignments
_HEATING = cfg['GPIO']['heat_pin']
_COOLING = cfg['GPIO']['cool_pin']

def hysteresis(c_set):
    if c_set:
        return cfg['behavior']['hysteresis_c']
    return cfg['behavior']['hysteresis_f']

def enable_heating(inputs):
    if (inputs['temp'] + inputs['hysteresis']) < inputs['set_temp']:
        GPIO.output(_HEATING, True)
        GPIO.output(_COOLING, False)
        db.execute('update config set status = ? where user_id = 1', [Status.heating.value])
        db.commit()
    elif (inputs['temp'] < inputs['set_temp']) and (inputs['status'] is Status.heating):
        GPIO.output(_HEATING, True)
        GPIO.output(_COOLING, False)
        db.execute('update config set status = ? where user_id = 1', [Status.heating.value])
        db.commit()
    return

def enable_cooling(inputs):
    if (inputs['temp'] + inputs['hysteresis']) > inputs['set_temp']:
        GPIO.output(_HEATING, False)
        GPIO.output(_COOLING, True)
        db.execute('update config set status = ? where user_id = 1', [Status.cooling.value])
        db.commit()
    elif (inputs['temp'] > inputs['set_temp']) and (inputs['status'] is Status.cooling):
        GPIO.output(_HEATING, False)
        GPIO.output(_COOLING, True)
        db.execute('update config set status = ? where user_id = 1', [Status.cooling.value])
        db.commit()
    return

def shutdown():
    GPIO.output(_HEATING, False)
    GPIO.output(_COOLING, False)
    db.execute('update config set status = ? where user_id = 1', [Status.off.value])
    db.commit()
    return

# Set up the GPIO pins
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup(_HEATING, GPIO.OUT)
GPIO.setup(_COOLING, GPIO.OUT)

# Get current mode, status and thermostat set point from config database
db = connect_db()
user_config = query_db('select * from users join config on users.user_id = config.user_id', one=True, db=db)
# If no config exists, turn off everything and exit
if user_config == None:
    shutdown()
    quit()
mode = Mode(user_config['mode'])
status = Status(user_config['status'])

# Quit if mode is set to OFF and turn off everything
if mode == Mode.off:
    shutdown()
    quit()

# Get Celsius / Fahrenheit setting
if user_config['celsius'] == 1:
    celsius_setting = True
else:
    celsius_setting = False
set_temp = user_config['set_temp']

# Get sensor temperature
temp = int(round(Sensor(celsius=celsius_setting).conditions['temp']))

# Logic to control heating / cooling
inputs = {
    'temp': temp,
    'set_temp': set_temp,
    'hysteresis': hysteresis(celsius_setting),
    'status': status
    }
print inputs
if mode is Mode.heat:
    if temp < set_temp:
        enable_heating(inputs)
    else:
        shutdown()
elif mode is Mode.cool:
    if temp > set_temp:
        enable_cooling(inputs)
    else:
        shutdown()
elif mode is Mode.heat_cool:
    if temp < set_temp:
        enable_heating(inputs)
    elif temp > set_temp:
        enable_cooling(inputs)
    else:
        shutdown()
else:
    print '* Error: We should not have gotten here *'
    shutdown()

# Do one last check to make sure heating and cooling are not both enabled
if (GPIO.input(_HEATING) and GPIO.input(_COOLING)):
    print '* Bad error: both heating and cooling enabled!'
    shutdown()

# Debug
print 'Status of heating pin is: {}'.format(GPIO.input(_HEATING))
print 'Status of cooling pin is: {}'.format(GPIO.input(_COOLING))
