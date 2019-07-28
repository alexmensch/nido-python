#   Nido, a Raspberry Pi-based home thermostat.
#
#   Copyright (C) 2016 Alex Marshall
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program.
#   If not, see <http://www.gnu.org/licenses/>.

import os
import logging

from nido.supervisor.config import HardwareConfig, DaemonConfig
from nido.lib import Mode, Status, c_to_f
from nido.lib.exceptions import ControllerError, SensorError
from nido.supervisor.thermostat import Thermostat

if "NIDO_TESTING" in os.environ:
    from nido.supervisor.simulator import FakeGPIO, FakeSensor as BME280

    GPIO = FakeGPIO(os.environ["NIDO_TESTING_GPIO"])
    BME280_OSAMPLE_8 = None
else:
    import RPi.GPIO as GPIO
    from nido.lib.Adafruit_BME280 import BME280, BME280_OSAMPLE_8


class Sensor(object):
    def __init__(self, mode=BME280_OSAMPLE_8):
        try:
            self.sensor = BME280(mode)
        except OSError:
            self.sensor = None
        self._l = logging.getLogger(__name__)
        return None

    def get_conditions(self):
        # Initialize response dict
        resp = {}

        # Could not connect to sensor
        if self.sensor is None:
            raise SensorError("Sensor was not detected.")

        temp_c = self.sensor.read_temperature()
        pressure_mb = round(self.sensor.read_pressure()) / 100
        relative_humidity = self.sensor.read_humidity()
        self._l.debug(
            "Sensor data: T = {}C | P = {} | RH = {}".format(
                temp_c, pressure_mb, relative_humidity
            )
        )
        conditions = {
            "temp": {"celsius": temp_c, "fahrenheit": c_to_f(temp_c)},
            "pressure_mb": pressure_mb,
            "relative_humidity": relative_humidity,
        }
        resp["conditions"] = conditions

        return resp


class Controller(object):
    """This is the controller code that determines whether the
    heating / cooling system should be enabled based on the thermostat
    set point."""

    def __init__(self):
        self._l = logging.getLogger(__name__)
        self._HEATING = HardwareConfig.GPIO_HEAT_PIN
        self._COOLING = HardwareConfig.GPIO_COOL_PIN

        # Set up the GPIO pins
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self._HEATING, GPIO.OUT)
        GPIO.setup(self._COOLING, GPIO.OUT)
        self._l.debug(
            "GPIO pins configured: heat = {} | cool = {}".format(
                self._HEATING, self._COOLING
            )
        )

        return

    def get_status(self):
        if GPIO.input(self._HEATING) and GPIO.input(self._COOLING):
            self._l.error("** Both heating and cooling pins enabled. **")
            self.shutdown()
            raise ControllerError(
                "Both heating and cooling pins were enabled. "
                "Both pins disabled as a precaution."
            )
        elif GPIO.input(self._HEATING):
            self._l.debug("Get status: {}".format(Status.Heating.name))
            return Status.Heating.value
        elif GPIO.input(self._COOLING):
            self._l.debug("Get state: {}".format(Status.Cooling.name))
            return Status.Cooling.value
        else:
            self._l.debug("Get state: {}".format(Status.Off.name))
            return Status.Off.value

    def _enable_heating(self, status, temp, set_temp, hysteresis):
        if (temp + hysteresis) < set_temp:
            GPIO.output(self._HEATING, True)
            GPIO.output(self._COOLING, False)
            self._l.debug("Enabled HEAT: {} < {}".format(temp + hysteresis, set_temp))
        elif (temp < set_temp) and (status is Status.Heating):
            GPIO.output(self._HEATING, True)
            GPIO.output(self._COOLING, False)
            self._l.debug(
                "Enabled HEAT: {} < {} and status = Heating".format(temp, set_temp)
            )
        return

    def _enable_cooling(self, status, temp, set_temp, hysteresis):
        if (temp + hysteresis) > set_temp:
            GPIO.output(self._HEATING, False)
            GPIO.output(self._COOLING, True)
        elif (temp > set_temp) and (status is Status.Cooling):
            GPIO.output(self._HEATING, False)
            GPIO.output(self._COOLING, True)
        return

    def shutdown(self):
        GPIO.output(self._HEATING, False)
        GPIO.output(self._COOLING, False)
        GPIO.cleanup()
        self._l.info("Shut down hardware GPIO pins.")
        return

    def update(self):
        settings = Thermostat.get_settings()
        try:
            mode = settings["set_mode"]
            status = self.get_status()
            temp = Sensor().get_conditions()["conditions"]["temp"]["celsius"]
            set_temp = settings["set_temp"]
            hysteresis = HardwareConfig.HYSTERESIS
        except KeyError as e:
            self.shutdown()
            raise ControllerError("Error reading Nido configuration: {}".format(e))
        except ControllerError:
            self.shutdown()
            raise

        if mode == Mode.Off.name:
            self._l.debug("Mode = Off | Set temp {}C".format(set_temp))
            self.shutdown()
        elif mode == Mode.Heat.name:
            self._l.debug("Mode = Heat | Set temp {}C".format(set_temp))
            if temp < set_temp:
                self._enable_heating(status, temp, set_temp, hysteresis)
            else:
                self.shutdown()
        else:
            # Additional modes can be enabled in future, eg. Mode.Cool,
            # Mode.Heat_Cool
            self.shutdown()

        return

    def daemon_running(self):
        return os.path.isfile(DaemonConfig.PID_FILE)
