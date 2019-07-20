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

import rpyc

from nido.supervisor.hardware import Controller, Sensor
from nido.supervisor.thermostat import Thermostat
from nido.lib.exceptions import ThermostatError
from nido.supervisor.datalogger import MQTTDataLogger


class NidoDaemonService(rpyc.Service):
    """Service class that is exposed via RPC.

    Methods act on the APScheduler service that is initialized on daemon
    startup. Static functions in the class are passed into scheduler
    jobs as resulting actions.

    Adapted from: https://github.com/agronholm/apscheduler/blob/master \
    /examples/rpc/server.py
    """

    def __init__(self, scheduler):
        self._scheduler = scheduler

    def __call__(self, conn):
        return self.__class__(self._scheduler)

    def add_job(self, callback, func, *args, **kwargs):
        job = self._scheduler.add_job(func, *args, **kwargs)
        callback(job)
        return None

    def modify_job(self, callback, job_id, jobstore=None, **changes):
        job = self._scheduler.modify_job(job_id, jobstore, **changes)
        callback(job)
        return None

    def reschedule_job(
        self, callback, job_id, jobstore=None, trigger=None, **trigger_args
    ):
        job = self._scheduler.reschedule_job(job_id, jobstore, trigger, **trigger_args)
        callback(job)
        return None

    def pause_job(self, callback, job_id, jobstore=None):
        job = self._scheduler.pause_job(job_id, jobstore)
        callback(job)
        return None

    def resume_job(self, callback, job_id, jobstore=None):
        job = self._scheduler.resume_job(job_id, jobstore)
        callback(job)
        return None

    def remove_job(self, job_id, jobstore=None):
        self._scheduler.remove_job(job_id, jobstore)
        return None

    def get_job(self, callback, job_id):
        job = self._scheduler.get_job(job_id)
        callback(job)
        return None

    def get_jobs(self, callback, jobstore=None):
        jobs = self._scheduler.get_jobs(jobstore)
        callback(jobs)
        return None

    @staticmethod
    def get_settings():
        return Thermostat.get_settings()

    @staticmethod
    def set_settings(set_temp=None, set_mode=None, celsius=None):
        try:
            Thermostat.set_settings(
                set_temp=set_temp, set_mode=set_mode, celsius=celsius
            )
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
    def get_controller_status():
        return Controller().get_status()

    @staticmethod
    def get_sensor_data():
        return Sensor().get_conditions()

    @staticmethod
    def wakeup():
        return Controller().update()

    @staticmethod
    def log_data(client):
        return MQTTDataLogger(client).publish_data()
