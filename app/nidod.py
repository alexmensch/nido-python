#!/usr/bin/python

import sys, time, signal, os
from datetime import datetime
from lib.Daemon import Daemon
from lib.Nido import Config, Controller
from apscheduler.schedulers.blocking import BlockingScheduler

class NidoDaemon(Daemon):
    def run(self):
        # Instantiate controller object
        self.controller = Controller()
        # Set up scheduler
        self.scheduler = BlockingScheduler({
            'apscheduler.job_defaults.coalesce': 'true',
            })

        # Get poll interval from config
        config = Config().get_config()
        poll_interval = config['schedule']['poll_interval']
        # Add scheduled job on configured polling interval
        self.scheduler.add_job(self.controller.update, trigger='interval', seconds=poll_interval)

        # Set up signal handler to trigger updates
        signal.signal(signal.SIGUSR1, self.signal_handler)
        # Log start time
        sys.stdout.write('{} [Info] Nido daemon started\n'.format(datetime.utcnow()))
        sys.stdout.flush()
        # Start scheduler (blocking)
        self.scheduler.start()

    def signal_handler(self, signum, stack):
        # Debug only, remove later
        self.scheduler.print_jobs()
        sys.stdout.flush()
        ##
        self.controller.update()
        return

    def quit(self):
        self.scheduler.shutdown(wait=False)
        Controller().shutdown()
        sys.stdout.write('{} [Info] Nido daemon shutdown\n'.format(datetime.utcnow()))
        return

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
