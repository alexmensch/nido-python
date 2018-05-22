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
#   along with this program.
#   If not, see <http://www.gnu.org/licenses/>.

from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from future import standard_library
standard_library.install_aliases()
from builtins import *

import sys
import logging
import logging.handlers
import os
from nido.daemon.base import Daemon
from nido.lib.nido import Config, Controller
from nido.lib.scheduler import NidoSchedulerService
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from rpyc.utils.server import ThreadedServer


class NidoDaemon(Daemon):
    def run(self):
        self._l.debug('Starting run loop for Nido daemon')
        self.controller = Controller()
        config = Config().get_config()
        poll_interval = config['schedule']['poll_interval']
        db_path = config['schedule']['db']
        rpc_port = config['schedule']['rpc_port']

        self.scheduler = BackgroundScheduler()
        jobstores = {
            'default': {'type': 'memory'},
            'schedule': SQLAlchemyJobStore(
                url='sqlite:///{}'.format(db_path)
            )
        }
        job_defaults = {'coalesce': True, 'misfire_grace_time': 10}
        self.scheduler.configure(jobstores=jobstores,
                                 job_defaults=job_defaults)
        self.scheduler.add_job(
            NidoSchedulerService.wakeup, trigger='interval',
            seconds=poll_interval, name='Poll'
        )
        self.scheduler.add_job(NidoSchedulerService.wakeup, name='Poll')
        self.scheduler.start()

        RPCserver = ThreadedServer(
            NidoSchedulerService(self.scheduler),
            port=rpc_port,
            protocol_config={
                'allow_public_attrs': True,
                'allow_pickle': True
            }
        )
        RPCserver.start()

    def quit(self):
        self.scheduler.shutdown()
        self.controller.shutdown()
        self._l.info('Nido daemon shutdown')
        self._l.info('********************')
        return


if __name__ == '__main__':
    config = Config().get_config()
    pid_file = config['daemon']['pid_file']
    work_dir = config['daemon']['work_dir']
    log_file = config['daemon']['log_file']

    handler = logging.handlers.WatchedFileHandler(log_file)
    formatter = logging.Formatter(
        fmt='%(asctime)s [%(levelname)s] %(name)s | %(message)s',
        datefmt='%d/%m/%Y %H:%M:%S'
    )
    handler.setFormatter(formatter)
    root = logging.getLogger()
    if 'NIDO_DEBUG' in os.environ:
        root.setLevel(logging.DEBUG)
    else:
        root.setLevel(logging.INFO)
    root.addHandler(handler)

    daemon = NidoDaemon(pid_file, work_dir, stderr=log_file, stdout=log_file)

    if 'start' == sys.argv[1]:
        daemon.start()
    elif 'stop' == sys.argv[1]:
        daemon.stop()
    elif 'restart' == sys.argv[1]:
        daemon.restart()
