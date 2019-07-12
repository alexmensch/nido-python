from __future__ import division
from builtins import object

import logging

from nidod import db
from nidod.config import HardwareConfig
from libnido import Mode
from libnido.exceptions import ThermostatError, DBError

logger = logging.getLogger(__name__)


class Thermostat(object):
    @staticmethod
    def get_settings():
        """Returns a dictionary of the thermostat settings."""
        try:
            state = db.get_settings()
        except DBError as e:
            raise ThermostatError(e)
        else:
            state['modes'] = HardwareConfig.MODES
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
            return db.set_settings(set_temp=set_temp,
                                   set_mode=set_mode,
                                   celsius=celsius)
        except DBError as e:
            raise ThermostatError(e)

    def set_temp(self, temp, scale):
        if scale.upper() == 'C':
            return self.set_settings(set_temp=temp)
        elif scale.upper() == 'F':
            # The following conversion duplicates the logic in nido.js
            celsius_temp = (temp - 32) * 5 / 9
            celsius_temp = round(celsius_temp * 10) / 10
            celsius_temp = float("{0:.1f}".format(celsius_temp))
            return self.set_settings(set_temp=celsius_temp)
        else:
            raise ThermostatError('Invalid temperature scale.')

    def set_mode(self, mode):
        modes = HardwareConfig.MODES

        for m in modes:
            if m.upper() == mode.upper():
                return self.set_settings(set_mode=m)

        raise ThermostatError('Invalid or unconfigured mode.')

    def set_scale(self, scale):
        if scale.upper() == 'C':
            return self.set_settings(celsius=True)
        elif scale.upper() == 'F':
            return self.set_settings(celsius=False)
        else:
            raise ThermostatError('Invalid temperature scale.')
