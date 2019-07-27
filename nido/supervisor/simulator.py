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

import yaml
from os import path


class FakeGPIO(object):
    def __init__(self, state_file):
        self._pins = {}
        self.BCM = None
        self.OUT = None
        self._state = state_file
        return None

    def setwarnings(self, bool):
        return None

    def setmode(self, mode):
        return None

    def setup(self, pin, mode):
        self._get_pins()
        if not self._pins or pin not in self._pins:
            self._set_pin(pin, False)
        return None

    def input(self, pin):
        self._get_pins()
        return self._pins[pin]

    def output(self, pin, state):
        self._set_pin(pin, state)
        return None

    def cleanup(self):
        return None

    def _set_pin(self, pin, state):
        self._pins[pin] = state
        self._write()
        return None

    def _get_pins(self):
        if path.exists(self._state):
            with open(self._state, "r") as f:
                self._pins = yaml.safe_load(f)
                if self._pins is None:
                    self._pins = {}
        return None

    def _write(self):
        with open(self._state, "w") as f:
            yaml.dump(self._pins, f, default_flow_style=False, indent=4)
        return None


class FakeSensor(object):
    def __init__(self, mode):
        self._temp = 17.17
        self._pressure = 101331.01
        self._humidity = 50.05
        return None

    def read_temperature(self):
        return self._temp

    def read_pressure(self):
        return self._pressure

    def read_humidity(self):
        return self._humidity
