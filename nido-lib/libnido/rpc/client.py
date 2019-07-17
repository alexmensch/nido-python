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

from libnido.exceptions import (
    SchedulerClientError,
    ThermostatClientError,
    ControllerError,
    ThermostatError,
    SensorError,
)
from libnido import Status


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
            config={
                "allow_all_attrs": True,
                "allow_public_attrs": True,
                "instantiate_custom_exceptions": True,
                "allow_pickle": True,
            },
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

    def get_settings(self):
        with self._rpc_session():
            return obtain(self.r.get_settings())

    def set_settings(self, set_temp=None, set_mode=None, celsius=None):
        with self._rpc_session():
            self.r.set_settings(set_temp=set_temp, set_mode=set_mode, celsius=celsius)
            return obtain(self.r.get_settings())

    def set_temp(self, temp, scale):
        with self._rpc_session():
            self.r.set_temp(temp, scale)
            return obtain(self.r.get_settings())

    def set_mode(self, mode):
        with self._rpc_session():
            self.r.set_mode(mode)
            return obtain(self.r.get_settings())

    def set_scale(self, scale):
        with self._rpc_session():
            self.r.set_scale(scale)
            return obtain(self.r.get_settings())

    def get_state(self):
        with self._rpc_session():
            status = self.r.get_controller_status()
            sensor_data = self.r.get_sensor_data()
            response = {}
            response["state"] = {"status": Status(status).name}
            response["state"].update(obtain(sensor_data))

        return response

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

    def get_scheduled_job(self, job_id):
        with self._rpc_session():
            job = self.r.get_job(job_id)
            job = obtain(job)
        return self._return_job(job)

    def add_scheduled_job(
        self,
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
            job = self.r.add_job(
                "libnido.rpc.server:NidoDaemonService.{}".format(func),
                args=args,
                name=name,
                jobstore="schedule",
                id=job_id,
                trigger="cron",
                day_of_week=day_of_week,
                hour=hour,
                minute=minute,
            )
            job = obtain(job)
        return self._return_job(job)

    def modify_scheduled_job(self, job_id, type=None, mode=None, temp=None, scale=None):
        func, args, name = self._parse_mode_settings(
            type, mode=mode, temp=temp, scale=scale
        )
        with self._rpc_session():
            job = self.r.modify_job(
                job_id,
                func="libnido.rpc.server:NidoDaemonService.{}".format(func),
                args=args,
                name=name,
            )
            job = obtain(job)
        return self._return_job(job)

    def reschedule_job(self, job_id, day_of_week=None, hour=None, minute=None):
        self._check_cron_parameters(day_of_week=day_of_week, hour=hour, minute=minute)
        with self._rpc_session():
            job = self.r.reschedule_job(
                job_id,
                trigger="cron",
                day_of_week=day_of_week,
                hour=hour,
                minute=minute,
            )
            job = obtain(job)
        return self._return_job(job)

    def pause_scheduled_job(self, job_id):
        with self._rpc_session():
            job = self.r.pause_job(job_id)
            job = obtain(job)
        return self._return_job(job)

    def resume_scheduled_job(self, job_id):
        with self._rpc_session():
            job = self.r.resume_job(job_id)
            job = obtain(job)
        return self._return_job(job)

    def remove_scheduled_job(self, job_id):
        with self._rpc_session():
            self.r.remove_job(job_id)
            return {
                "message": "Job removed successfully.",
                "id": "{}".format(job_id),
            }

    def _return_job(self, job):
        return self._jsonify_job(job)

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
