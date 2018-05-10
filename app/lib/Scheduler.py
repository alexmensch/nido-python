import rpyc
from functools import wraps
from Nido import Config, Controller

class NidoSchedulerService(rpyc.Service):
    """Service class that is exposed via RPC.

    Methods act on the APScheduler service that is initialized on daemon startup.
    Static functions in the class are be passed into scheduler jobs as resulting actions.

    Adapted from: https://github.com/agronholm/apscheduler/blob/master/examples/rpc/server.py
    """

    def __init__(self, scheduler):
        self._scheduler = scheduler

    def __call__(self, conn):
        return self.__class__(self._scheduler)

    def exposed_add_job(self, func, *args, **kwargs):
        return self._scheduler.add_job(func, *args, **kwargs)

    def exposed_modify_job(self, job_id, jobstore=None, **changes):
        return self._scheduler.modify_job(job_id, jobstore, **changes)

    def exposed_reschedule_job(self, job_id, jobstore=None, trigger=None, **trigger_args):
        return self._scheduler.reschedule_job(job_id, jobstore, trigger, **trigger_args)

    def exposed_pause_job(self, job_id, jobstore=None):
        return self._scheduler.pause_job(job_id, jobstore)

    def exposed_resume_job(self, job_id, jobstore=None):
        return self._scheduler.resume_job(job_id, jobstore)

    def exposed_remove_job(self, job_id, jobstore=None):
        self._scheduler.remove_job(job_id, jobstore)

    def exposed_get_job(self, job_id):
        return self._scheduler.get_job(job_id)

    def exposed_get_jobs(self, jobstore=None):
        return self._scheduler.get_jobs(jobstore)

    @staticmethod
    def set_temp(temp, scale):
        return Config().set_temp(temp, scale)

    @staticmethod
    def set_mode(mode):
        return Config().set_mode(mode)

    @staticmethod
    def wakeup():
        Controller().update()
        return

def keepalive(func):
    """Decorator to ensure that RPC connection is active when calls are made."""

    @wraps(func)
    def check_connection(self, *args, **kwargs):
        if not self._is_connected():
            self._connect()
        return func(self, *args, **kwargs)

    return check_connection

class NidoDaemonServiceError(Exception):
    """Exception class for errors generated by the daemon RPC service."""

    def __init__(self, msg):
        self.msg = msg
        return

    def __str__(self):
        return repr(self.msg)

class NidoDaemonService:
    """Wrapper service to view/add/modify/delete daemon scheduler jobs via RPC."""

    def __init__(self):
        self._config = Config().get_config()
        self._connect()
        return

    @keepalive
    def wakeup(self):
        return self._connection.root.add_job('nidod:NidoSchedulerService.wakeup')

    @keepalive
    def add_scheduled_job(self, type, day_of_week=None, hour=None, minute=None, job_id=None, mode=None, temp=None, scale=None):
        if type != 'mode' and type != 'temp':
            raise NidoDaemonServiceError('Invalid job type specified: {}'.format(type))
        
        if type == 'mode':
            return self._connection.root.add_job('nidod:NidoSchedulerService.set_mode', args=[mode], name='Mode', jobstore='schedule', id=job_id, trigger='cron', day_of_week=day_of_week, hour=hour, minute=minute)
        elif type == 'temp':
            return self._connection.root.add_job('nidod:NidoSchedulerService.set_temp', args=[temp, scale], name='Temp', jobstore='schedule', id=job_id, trigger='cron', day_of_week=day_of_week, hour=hour, minute=minute)

    @keepalive
    def modify_scheduled_job(self, job_id, type, mode=None, temp=None, scale=None):
        if type != 'mode' and type != 'temp':
            raise NidoDaemonServiceError('Invalid job type specified: {}'.format(type))

        if type == 'mode':
            return self._connection.root.modify_job(job_id, args=[mode])
        elif type == 'temp':
            return self._connection.root.modify_job(job_id, args=[temp, scale])

    @keepalive
    def reschedule_job(self, job_id, day_of_week=None, hour=None, minute=None):
        trigger = CronTrigger(day_of_week=day_of_week, hour=hour, minute=minute)
        return self._connection.root.reschedule_job(job_id, trigger=trigger)

    @keepalive
    def pause_scheduled_job(self, job_id):
        return self._connection.root.pause_job(job_id)

    @keepalive
    def resume_scheduled_job(self, job_id):
        return self._connection.root.resume_job(job_id)

    @keepalive
    def remove_scheduled_job(self, job_id):
        return self._connection.root.remove_job(job_id)

    @keepalive
    def get_scheduled_jobs(self):
        return self._connection.root.get_jobs()

    @keepalive
    def get_scheduled_job(self, job_id):
        return self._connection.root.get_job(job_id)

    def _is_connected(self):
        return not self._connection.closed

    def _connect(self):
        self._connection = rpyc.connect(self._config['schedule']['rpc_host'], self._config['schedule']['rpc_port'])
