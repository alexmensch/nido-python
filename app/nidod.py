#!/usr/bin/python

import sys, time, signal, os
from datetime import datetime
from lib.Daemon import Daemon
from lib.Nido import Config, Controller
from apscheduler.schedulers.blocking import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
import rpyc
from rpyc.utils.server import ThreadedServer

class NidoDaemon(Daemon):
    def run(self):
        # Get config
        config = Config().get_config()
        poll_interval = config['schedule']['poll_interval']
        db_path = config['schedule']['db']
        # Instantiate controller object
        self.controller = Controller()
        # Set up scheduler
        self.scheduler = BackgroundScheduler()
        jobstores = {
                'default': {'type': 'memory'},
                'schedule': SQLAlchemyJobStore(url='sqlite:///{}'.format(db_path))
                }
        job_defaults = {
                'coalesce': True
                }
        self.scheduler.configure(jobstores=jobstores, job_defaults=job_defaults)

        # Add scheduled job on configured polling interval
        self.scheduler.add_job(self.controller.update, trigger='interval', seconds=poll_interval)

        # Log start time
        sys.stdout.write('{} [Info] Nido daemon started\n'.format(datetime.utcnow()))
        sys.stdout.flush()

        # Start scheduler and RPyC service
        self.scheduler.start()
        protocol_config = {'allow_public_attrs': True}
        server = ThreadedServer(SchedulerService, port=12345, protocol_config=protocol_config)
        server.start()

    def quit(self):
        self.scheduler.shutdown()
        Controller().shutdown()
        sys.stdout.write('{} [Info] Nido daemon shutdown\n'.format(datetime.utcnow()))
        return

# From: https://github.com/agronholm/apscheduler/blob/master/examples/rpc/server.py
#
class SchedulerService(rpyc.Service):
    def exposed_add_job(self, func, *args, **kwargs):
        return scheduler.add_job(func, *args, **kwargs)

    def exposed_modify_job(self, job_id, jobstore=None, **changes):
        return scheduler.modify_job(job_id, jobstore, **changes)

    def exposed_reschedule_job(self, job_id, jobstore=None, trigger=None, **trigger_args):
        return scheduler.reschedule_job(job_id, jobstore, trigger, **trigger_args)

    def exposed_pause_job(self, job_id, jobstore=None):
        return scheduler.pause_job(job_id, jobstore)

    def exposed_resume_job(self, job_id, jobstore=None):
        return scheduler.resume_job(job_id, jobstore)

    def exposed_remove_job(self, job_id, jobstore=None):
        scheduler.remove_job(job_id, jobstore)

    def exposed_get_job(self, job_id):
        return scheduler.get_job(job_id)

    def exposed_get_jobs(self, jobstore=None):
        return scheduler.get_jobs(jobstore)

###
# Start of execution
###

config = Config().get_config()
pid_file = config['daemon']['pid_file']
work_dir = config['daemon']['work_dir']
log_file = config['daemon']['log_file']
daemon = NidoDaemon(pid_file, work_dir, stderr=log_file, stdout=log_file)

if 'start' == sys.argv[1]:
    daemon.start()
elif 'stop' == sys.argv[1]:
    daemon.stop()
elif 'restart' == sys.argv[1]:
    daemon.restart()
