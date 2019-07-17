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
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.date import DateTrigger
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
    def __init__(self, host, port, json=False):
        self._json = json
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

    def process_jobs(self, jobs):
        if self._json:
            return self._jsonify_jobs(jobs)
        return jobs

    def get_scheduled_jobs(self, jobstore=None):
        with self._rpc_session():
            self.r.get_jobs(self.process_jobs, jobstore=jobstore)

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
                "nidod.lib.rpc.server:NidoDaemonService.{}".format(func),
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
                func="nidod.lib.rpc.server:NidoDaemonService.{}".format(func),
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
            if self._json:
                return {
                    "message": "Job removed successfully.",
                    "id": "{}".format(job_id),
                }
        return None

    def _return_job(self, job):
        if self._json:
            return self._jsonify_job(job)
        return job

    def _jsonify_job(self, j):
        if j is None:
            raise SchedulerClientError("No job exists with that ID.")
        if isinstance(j.trigger, DateTrigger):
            trigger = {"timezone": str(j.trigger.run_date.tzinfo)}
        else:
            trigger_start_date = (
                j.trigger.start_date.strftime("%m/%d/%Y %H:%M:%S")
                if j.trigger.start_date
                else None
            )
            trigger_end_date = (
                j.trigger.end_date.strftime("%m/%d/%Y %H:%M:%S")
                if j.trigger.end_date
                else None
            )
            trigger = {
                "start_date": trigger_start_date,
                "end_date": trigger_end_date,
                "timezone": str(j.trigger.timezone),
            }

        if isinstance(j.trigger, CronTrigger):
            trigger["cron"] = {}
            for f in j.trigger.fields:
                trigger["cron"][f.name] = str(f)
        elif isinstance(j.trigger, IntervalTrigger):
            trigger_interval = str(j.trigger.interval) if j.trigger.interval else None
            trigger["interval"] = trigger_interval
        elif isinstance(j.trigger, DateTrigger):
            trigger["run_date"] = j.trigger.run_date.strftime("%m/%d/%Y %H:%M:%S")
        else:
            raise SchedulerClientError(
                "Unknown trigger type: {}".format(type(j.trigger))
            )

        job = {
            "id": j.id,
            "name": j.name,
            "args": j.args,
            "next_run_time": (
                j.next_run_time.strftime("%m/%d/%Y %H:%M:%S")
                if j.next_run_time
                else None
            ),
            "trigger": trigger,
        }

        return job

    def _jsonify_jobs(self, jobs):
        job_list = []
        for j in jobs:
            if j is None:
                continue
            job_list.append(self._jsonify_job(j))
        return job_list

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
