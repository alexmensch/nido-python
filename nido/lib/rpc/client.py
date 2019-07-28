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

from contextlib import contextmanager
import logging

import rpyc
from rpyc.utils.classic import obtain
from apscheduler.jobstores.base import JobLookupError, ConflictingIdError

from nido.lib.exceptions import (
    SchedulerClientError,
    ThermostatClientError,
    ControllerError,
    ThermostatError,
    SensorError,
)
from nido.lib import Status


class NidoDaemonRPCClient(object):
    def __init__(self, host, port):
        self._host = host
        self._port = port
        self._l = logging.getLogger(__name__)
        return None

    def _is_connected(self):
        return not self._connection.closed

    def _connect(self):
        self._connection = rpyc.connect(
            self._host,
            self._port,
            config={"allow_pickle": True, "instantiate_custom_exceptions": True},
        )
        self.r = self._connection.root
        return None

    def _disconnect(self):
        if self._is_connected:
            self._connection.close()
        return None

    @contextmanager
    def _rpc_session(self):
        self._connect()
        try:
            yield
        except (ControllerError, ThermostatError, SensorError) as e:
            raise ThermostatClientError(e)
        except (JobLookupError, ConflictingIdError) as e:
            raise SchedulerClientError(e)
        finally:
            pass
            self._disconnect()
        return None


class ThermostatClient(NidoDaemonRPCClient):
    """RPC client service to get and set thermostat settings."""

    def get_mode(self):
        with self._rpc_session():
            mode = self.r.get_mode()
        return int(mode)

    def set_mode(self, mode):
        with self._rpc_session():
            self.r.set_mode(mode)
        return None

    def get_temp_units(self):
        with self._rpc_session():
            celsius = self.r.get_temp_units()
        return celsius

    def set_temp_units(self, units):
        with self._rpc_session():
            self.r.set_temp_units(units)

    def get_set_temp(self):
        with self._rpc_session():
            set_temp = self.r.get_set_temp()
        return float(set_temp)

    def set_temp(self, temp, scale):
        with self._rpc_session():
            self.r.set_temp(temp, scale)

    def get_conditions(self):
        with self._rpc_session():
            sensor_data = self.r.get_sensor_data()
            conditions = obtain(sensor_data)
        return conditions

    def get_state(self):
        with self._rpc_session():
            status = int(self.r.get_controller_status())
        return status

    def wakeup(self):
        with self._rpc_session():
            self.r.wakeup()
        return None


class SchedulerClient(NidoDaemonRPCClient):
    """RPC client service to view/add/modify/delete daemon scheduler
    jobs.
    """

    def get_scheduled_jobs(self, callback, jobstore=None):
        with self._rpc_session():
            self.r.get_jobs(callback, jobstore=jobstore)
        return None

    def get_scheduled_job(self, callback, job_id):
        with self._rpc_session():
            self.r.get_job(callback, job_id)
        return None

    def add_scheduled_job(
        self,
        callback,
        type,
        day_of_week=None,
        hour=None,
        minute=None,
        job_id=None,
        mode=None,
        temp=None,
        scale=None,
    ):
        func, args, name = self._parse_mode_settings(
            type, mode=mode, temp=temp, scale=scale
        )
        self._check_cron_parameters(day_of_week=day_of_week, hour=hour, minute=minute)
        with self._rpc_session():
            self.r.add_job(
                callback,
                "nido.lib.rpc.server:NidoDaemonService.{}".format(func),
                args=args,
                name=name,
                jobstore="schedule",
                id=job_id,
                trigger="cron",
                day_of_week=day_of_week,
                hour=hour,
                minute=minute,
            )
        return None

    def modify_scheduled_job(
        self, callback, job_id, type=None, mode=None, temp=None, scale=None
    ):
        func, args, name = self._parse_mode_settings(
            type, mode=mode, temp=temp, scale=scale
        )
        with self._rpc_session():
            self.r.modify_job(
                callback,
                job_id,
                func="nido.lib.rpc.server:NidoDaemonService.{}".format(func),
                args=args,
                name=name,
            )
        return None

    def reschedule_job(
        self, callback, job_id, day_of_week=None, hour=None, minute=None
    ):
        self._check_cron_parameters(day_of_week=day_of_week, hour=hour, minute=minute)
        with self._rpc_session():
            self.r.reschedule_job(
                callback,
                job_id,
                trigger="cron",
                day_of_week=day_of_week,
                hour=hour,
                minute=minute,
            )
        return None

    def pause_scheduled_job(self, callback, job_id):
        with self._rpc_session():
            self.r.pause_job(callback, job_id)
        return None

    def resume_scheduled_job(self, callback, job_id):
        with self._rpc_session():
            self.r.resume_job(callback, job_id)
        return None

    def remove_scheduled_job(self, job_id):
        with self._rpc_session():
            self.r.remove_job(job_id)
        return None

    def _parse_mode_settings(self, type, mode=None, temp=None, scale=None):
        if type == "mode":
            if mode is None:
                raise SchedulerClientError("No mode specified.")
            else:
                func = "set_mode"
                args = [mode]
                name = "Mode: {}".format(mode.upper())
        elif type == "temp":
            if temp is None or scale is None:
                raise SchedulerClientError(
                    "Both temperature value and scale are required."
                )
            else:
                func = "set_temp"
                args = [temp, scale]
                name = "Temp: {:.1f}{}".format(float(temp), scale.upper())
        else:
            raise SchedulerClientError("Invalid job type specified: {}".format(type))
        return (func, args, name)

    def _check_cron_parameters(self, day_of_week=None, hour=None, minute=None):
        if day_of_week is None and hour is None and minute is None:
            raise SchedulerClientError("No timing specified for job.")
        return None
