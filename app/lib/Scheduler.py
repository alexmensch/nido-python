import rpyc
from Nido import Config, Controller
from functools import wraps

# Adapted from: https://github.com/agronholm/apscheduler/blob/master/examples/rpc/server.py
#
class NidoSchedulerService(rpyc.Service):
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
        return self._scheduler.get_jobs(jobstore)\

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

class NidoDaemonService:
    def __init__(self):
        self._config = Config().get_config()
        self._connection = self._connect()
        return

    @keepalive
    def wakeup(self):
        return self._connection.root.add_job('nidod:nss.wakeup')

    def _is_connected(self):
        return not self._connection.closed

    def _connect(self):
        return rpyc.connect(self._config['schedule']['rpc_host'], self._config['schedule']['rpc_port'])

# Decorator to ensure that RPC connection is kept active
#
def keepalive(func):
    @wraps(func)
    def check_connection(self, *args, **kwargs):
        if not self._is_connected():
            self._connection = self._connect()
        else:
            return func(self, *args, **kwargs)

    return check_connection
