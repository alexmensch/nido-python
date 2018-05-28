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

from __future__ import absolute_import
from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from future import standard_library
standard_library.install_aliases()
from builtins import *

import rpyc
from nidod.lib.hardware import Controller
from nidod.lib.thermostat import Thermostat


class NidoDaemonService(rpyc.Service):
    """Service class that is exposed via RPC.

    Methods act on the APScheduler service that is initialized on daemon
    startup. Static functions in the class are be passed into scheduler
    jobs as resulting actions.

    Adapted from: https://github.com/agronholm/apscheduler/blob/master \
    /examples/rpc/server.py
    """

    def __init__(self, scheduler):
        self._scheduler = scheduler

    def __call__(self, conn):
        return self.__class__(self._scheduler)

    def add_job(self, func, *args, **kwargs):
        return self._scheduler.add_job(func, *args, **kwargs)

    def modify_job(self, job_id, jobstore=None, **changes):
        return self._scheduler.modify_job(job_id, jobstore, **changes)

    def reschedule_job(self, job_id, jobstore=None, trigger=None,
                       **trigger_args):
        return self._scheduler.reschedule_job(job_id, jobstore, trigger,
                                              **trigger_args)

    def pause_job(self, job_id, jobstore=None):
        return self._scheduler.pause_job(job_id, jobstore)

    def resume_job(self, job_id, jobstore=None):
        return self._scheduler.resume_job(job_id, jobstore)

    def remove_job(self, job_id, jobstore=None):
        self._scheduler.remove_job(job_id, jobstore)

    def get_job(self, job_id):
        return self._scheduler.get_job(job_id)

    def get_jobs(self, jobstore=None):
        return self._scheduler.get_jobs(jobstore)

    @staticmethod
    def get_settings():
        return Thermostat.get_settings()

    @staticmethod
    def set_settings(set_temp=temp, set_mode=mode, celsius=celsius):
        try:
            Thermostat.set_settings(set_temp=temp,
                                    set_mode=mode,
                                    celsius=celsius)
        except ThermostatError:
            raise
        else:
            return NidoDaemonService.wakeup()

    @staticmethod
    def set_temp(temp, scale):
        try:
            Thermostat().set_temp(temp, scale)
        except ThermostatError:
            raise
        else:
            return NidoDaemonService.wakeup()

    @staticmethod
    def set_mode(mode):
        try:
            Thermostat().set_mode(mode)
        except ThermostatError:
            raise
        else:
            return NidoDaemonService.wakeup()

    @staticmethod
    def set_scale(scale):
        Thermostat().set_scale(scale)

    @staticmethod
    def wakeup():
        return Controller().update()
