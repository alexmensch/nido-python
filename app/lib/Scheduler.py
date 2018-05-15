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
import json
from functools import wraps
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.date import DateTrigger
from apscheduler.jobstores.base import JobLookupError, ConflictingIdError
from nido import Config, Controller


class NidoSchedulerService(rpyc.Service):
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
    def set_temp(temp, scale):
        return Config().set_temp(temp, scale)

    @staticmethod
    def set_mode(mode):
        return Config().set_mode(mode)

    @staticmethod
    def wakeup():
        return Controller().update()


def keepalive(func):
    """Decorator to ensure that RPC connection is active when calls
    are made.

    The output is converted to JSON if the instance variable self._json
    is True. The base methods return either a Job object or a list of
    Job objects from the APScheduler package.
    """

    @wraps(func)
    def check_connection(self, *args, **kwargs):
        try:
            return func(self, *args, **kwargs)
        except EOFError:
            self._connect()
            return func(self, *args, **kwargs)

    return check_connection


def raise_exceptions(func):
    @wraps(func)
    def catch_exceptions(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except (JobLookupError, ConflictingIdError) as e:
            raise NidoDaemonServiceError('{}'.format(e.message))

    return catch_exceptions


class NidoDaemonServiceError(Exception):
    """Exception class for errors generated by the daemon RPC
    service."""

    def __init__(self, msg):
        self.msg = msg
        return

    def __str__(self):
        return repr(self.msg)


class NidoDaemonService:
    """Wrapper service to view/add/modify/delete daemon scheduler jobs
    via RPC."""

    def __init__(self, json=False):
        self._json = json
        self._config = Config().get_config()
        self._connect()
        return

    @keepalive
    def wakeup(self):
        job = self._connection.root \
              .add_job('nidod:NidoSchedulerService.wakeup')
        if self._json:
            return self._jsonify_job(job)
        return job

    @keepalive
    @raise_exceptions
    def get_scheduled_jobs(self, jobstore=None):
        jobs = self._connection.root.get_jobs(jobstore=jobstore)
        if self._json:
            return self._jsonify_jobs(jobs)
        return jobs

    @keepalive
    @raise_exceptions
    def get_scheduled_job(self, job_id):
        return self._return_job(self._connection.root.get_job(job_id))

    @keepalive
    @raise_exceptions
    def add_scheduled_job(self, type, day_of_week=None, hour=None, minute=None,
                          job_id=None, mode=None, temp=None, scale=None):
        if type == 'mode':
            if mode is None:
                raise NidoDaemonServiceError('No mode specified.')
            else:
                func = 'set_mode'
                args = [mode]
                name = 'Mode: {}'.format(mode.lower())
        elif type == 'temp':
            if temp is None or scale is None:
                raise NidoDaemonServiceError('Both temperature value and \
                                              scale are required.')
            else:
                func = 'set_temp'
                args = [temp, scale]
                name = 'Temp: {:.1f}{}'.format(float(temp), scale.upper())
        else:
            raise NidoDaemonServiceError('Invalid job type specified: {}' \
                                         .format(type))

        if day_of_week is None and hour is None and minute is None:
            raise NidoDaemonServiceError('No timing specified for job.')

        job = self._connection.root.add_job('nidod:NidoSchedulerService.{}' \
                                            .format(func), args=args,
                                            name=name, jobstore='schedule',
                                            id=job_id, trigger='cron',
                                            day_of_week=day_of_week, hour=hour,
                                            minute=minute)
        return self._return_job(job)

    @keepalive
    @raise_exceptions
    def modify_scheduled_job(self, job_id, type, mode=None, temp=None,
                             scale=None):
        ######
        # TODO
        ######
        if type == 'mode':
            return self._connection.root.modify_job(job_id, args=[mode])
        elif type == 'temp':
            return self._connection.root.modify_job(job_id, args=[temp, scale])
        else:
            raise NidoDaemonServiceError('Invalid job type specified: {}' \
                                         .format(type))

    @keepalive
    @raise_exceptions
    def reschedule_job(self, job_id, day_of_week=None, hour=None, minute=None):
        ######
        # TODO
        ######
        return self._connection.root.reschedule_job(job_id, trigger='cron',
                                                    day_of_week=day_of_week,
                                                    hour=hour, minute=minute)

    @keepalive
    @raise_exceptions
    def pause_scheduled_job(self, job_id):
        return self._return_job(self._connection.root.pause_job(job_id))

    @keepalive
    @raise_exceptions
    def resume_scheduled_job(self, job_id):
        return self._return_job(self._connection.root.resume_job(job_id))

    @keepalive
    @raise_exceptions
    def remove_scheduled_job(self, job_id):
        self._connection.root.remove_job(job_id)
        if self._json:
            return {'message': 'Job removed successfully.', 'id': '{}' \
                                                            .format(job_id)}
        return

    def _return_job(self, job):
        if self._json:
            return self._jsonify_job(job)
        return job

    def _is_connected(self):
        return not self._connection.closed

    def _connect(self):
        self._connection = rpyc.connect(self._config['schedule']['rpc_host'],
                                        self._config['schedule']['rpc_port'],
                                        config={'allow_public_attrs': True,
                                        'instantiate_custom_exceptions': True})

    def _jsonify_job(self, j):
        if isinstance(j.trigger, DateTrigger):
            trigger = {
                'timezone': str(j.trigger.run_date.tzinfo)
            }
        else:
            trigger_start_date = j.trigger.start_date. \
                                 strftime('%m/%d/%Y %H:%M:%S') \
                                 if j.trigger.start_date else None
            trigger_end_date = j.trigger.end_date.strftime('%m/%d/%Y %H:%M:%S') \
                               if j.trigger.end_date else None
            trigger = {
                'start_date': trigger_start_date,
                'end_date': trigger_end_date,
                'timezone': str(j.trigger.timezone)
            }

        if isinstance(j.trigger, CronTrigger):
            trigger['cron'] = {}
            for f in j.trigger.fields:
                trigger['cron'][f.name] = str(f)
        elif isinstance(j.trigger, IntervalTrigger):
            trigger_interval = str(j.trigger.interval) if j.trigger.interval \
                                                       else None
            trigger['interval'] = trigger_interval
        elif isinstance(j.trigger, DateTrigger):
            trigger['run_date'] = j.trigger.run_date \
                                  .strftime('%m/%d/%Y %H:%M:%S')
        else:
            raise NidoDaemonServiceError('Unknown trigger type: {}' \
                                         .format(type(j.trigger)))

        job = {
            'id': j.id,
            'name': j.name,
            'args': j.args,
            'next_run_time': j.next_run_time.strftime('%m/%d/%Y %H:%M:%S') \
                             if j.next_run_time else None,
            'trigger': trigger
        }

        return job

    def _jsonify_jobs(self, jobs):
        job_list = []
        for j in jobs:
            if j is None:
                continue
            job_list.append(self._jsonify_job(j))
        return job_list
