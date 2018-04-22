#!/usr/bin/python

import sys, time, signal, os
from datetime import datetime
from lib.Daemon import Daemon
from lib.Nido import Config, Controller
from apscheduler.schedulers.background import BackgroundScheduler

class NidoDaemon(Daemon):
    def run(self):
        # Get poll interval from config
        try:
            config = Config().get_config()
        except Exception as e:
            sys.stderr.write('{} [Error] Unable to read configuration file: {}\n'.format(datetime.utcnow(), e))
            self.stop()
        else:
            try:
                poll_interval = config['daemon']['poll_interval']
            except Exception as e:
                sys.stderr.write('{} [Error] Unable to read daemon poll_interval from config file: {}\n'.format(datetime.utcnow(), e))
                self.stop()

        # Instantiate controller object
        try:
            self.controller = Controller()
        except Exception as e:
            sys.stderr.write('{} [Error] Unable to instantiate Controller: {}\n'.format(datetime.utcnow(), e))
            self.stop()

        # Set up signal handler to trigger updates
        signal.signal(signal.SIGUSR1, self.signal_handler)
        # Log start time
        sys.stdout.write('{} [Info] Nido daemon started\n'.format(datetime.utcnow()))
        sys.stdout.flush()

        ###
        # Set up scheduler
        self.scheduler = BackgroundScheduler({
            'apscheduler.job_defaults.coalesce': 'true',
            })
        self.scheduler.add_job(self.controller.update(), id='poll', trigger='interval', seconds=poll_interval)
        self.scheduler.start()
        sys.stdout.write(self.scheduler.print_jobs())
        sys.stdout.flush()

    def signal_handler(self, signum, stack):
        self.controller.update()
        return

    def quit(self):
        self.scheduler.shutdown(wait=False)
        try:
            Controller().shutdown()
        except Exception as e:
            sys.stderr.write('{} [Error] *CRITICAL*: unable to shutdown GPIO pins: {}\n'.format(datetime.utcnow(), e))
        else:
            # Log stop time
            sys.stdout.write('{} [Info] Nido daemon shutdown\n'.format(datetime.utcnow()))
            sys.stdout.flush()
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
