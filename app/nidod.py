#!/usr/bin/python

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
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.

import sys
from datetime import datetime
from lib.Daemon import Daemon
from lib.Nido import Config, Controller
from lib.Scheduler import NidoSchedulerService
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from rpyc.utils.server import ThreadedServer

class NidoDaemon(Daemon):
    def run(self):
        self.controller = Controller()
        config = Config().get_config()
        poll_interval = config['schedule']['poll_interval']
        db_path = config['schedule']['db']

        self.scheduler = BackgroundScheduler()
        jobstores = {
                'default': {'type': 'memory'},
                'schedule': SQLAlchemyJobStore(url='sqlite:///{}'.format(db_path))
                }
        job_defaults = {
                'coalesce': True
                }
        self.scheduler.configure(jobstores=jobstores, job_defaults=job_defaults)
        self.scheduler.add_job(self.controller.update, trigger='interval', seconds=poll_interval, name='Poll')
        self.scheduler.start()
        
        RPCserver = ThreadedServer(NidoSchedulerService(self.scheduler), port=49152, protocol_config={'allow_public_attrs': True})

        sys.stdout.write('{} [Info] Nido daemon started\n'.format(datetime.utcnow()))
        sys.stdout.flush()

        RPCserver.start()

    def quit(self):
        self.scheduler.shutdown()
        self.controller.shutdown()
        sys.stdout.write('{} [Info] Nido daemon shutdown\n'.format(datetime.utcnow()))
        sys.stdout.flush()
        return

if __name__ == '__main__':
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
