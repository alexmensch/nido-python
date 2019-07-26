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

from nido.supervisor import db
from nido.supervisor.config import HardwareConfig
from nido.lib import Mode, f_to_c
from nido.lib.exceptions import ThermostatError, DBError


class Thermostat(object):
    @staticmethod
    def get_settings():
        """Returns a dictionary of the thermostat settings."""
        try:
            state = db.get_settings()
        except DBError as e:
            raise ThermostatError(e)
        else:
            state["modes"] = HardwareConfig.MODES
            return state

    @staticmethod
    def set_settings(set_temp=None, set_mode=None, celsius=None):
        """Set thermostat settings directly without any error-checking
        or temperature scale conversion.

        If the input needs to be sanitized, use set_temp(), set_mode()
        or set_scale() instead.
        """
        set_mode = Mode[set_mode].value if set_mode is not None else None
        try:
            return db.set_settings(
                set_temp=set_temp, set_mode=set_mode, celsius=celsius
            )
        except DBError as e:
            raise ThermostatError(e)

    @staticmethod
    def get_set_temp():
        try:
            settings = db.get_settings()
        except DBError as e:
            raise ThermostatError(e)
        else:
            return settings["set_temp"]

    def set_temp(self, temp, scale):
        if scale.upper() == "C":
            return self.set_settings(set_temp=temp)
        elif scale.upper() == "F":
            return self.set_settings(set_temp=f_to_c(temp))
        else:
            raise ThermostatError("Invalid temperature scale.")

    @staticmethod
    def get_mode():
        try:
            settings = db.get_settings()
        except DBError as e:
            raise ThermostatError(e)
        else:
            return Mode[settings["set_mode"]].value

    def set_mode(self, mode):
        """Set the thermostat mode.

        If we can't find a match against the configured modes
        in HardwareConfig.MODES, raise an exception.
        """
        modes = HardwareConfig.MODES

        for m in modes:
            if m.upper() == mode.upper():
                return self.set_settings(set_mode=m)

        raise ThermostatError("Invalid or unconfigured mode.")
