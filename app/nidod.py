#!/usr/bin/python

import sys, time, signal
from datetime import datetime
from lib.Daemon import Daemon
from lib.Nido import Config, Controller

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

        ###
        # Run loop
        while True:
            try:
                self.controller.update()
            except Exception as e:
                sys.stderr.write('{} [Error] Controller update failed: {}\n'.format(datetime.utcnow(), e))
            time.sleep(poll_interval)
        #
        ###

    def signal_handler(self, signum, stack):
        # No action is necessary here. The signal interrupt breaks code execution out of the time.sleep()
        # call in the run loop the vast majority of the time, triggering an immediate controller update
        # and a reset of the poll interval.
        pass

    def quit(self):
        try:
            Controller().shutdown()
        except Exception as e:
            sys.stderr.write('{} [Error] *CRITICAL*: unable to shutdown GPIO pins: {}\n'.format(datetime.utcnow(), e))
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
