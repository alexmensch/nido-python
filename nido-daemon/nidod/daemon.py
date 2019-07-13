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

import paho.mqtt.client as mqtt
from rpyc.utils.server import ThreadedServer
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from nidod import Daemon
from nidod.config import SchedulerConfig, DaemonConfig, MQTTConfig
from nidod.hardware import Controller
from nidod.rpc.server import NidoDaemonService


class NidoDaemon(Daemon):
    def run(self):
        self._l.debug("Starting run loop for Nido daemon")
        self.controller = Controller()

        self.MQTTclient = mqtt.Client(MQTTConfig.CLIENT_NAME, clean_session=False)
        self.MQTTclient.enable_logger()
        self.MQTTclient.connect_async(
            MQTTConfig.HOSTNAME,
            port=int(MQTTConfig.PORT),
            keepalive=MQTTConfig.KEEPALIVE,
        )

        self.scheduler = BackgroundScheduler()
        jobstores = {
            "default": {"type": "memory"},
            "schedule": SQLAlchemyJobStore(
                url="sqlite:///{}".format(DaemonConfig.DB_PATH)
            ),
        }
        job_defaults = {"coalesce": True, "misfire_grace_time": 10}
        self.scheduler.configure(jobstores=jobstores, job_defaults=job_defaults)
        self.scheduler.add_job(NidoDaemonService.wakeup, name="Poll")
        self.scheduler.add_job(
            NidoDaemonService.wakeup,
            trigger="interval",
            seconds=SchedulerConfig.POLL_INTERVAL,
            name="Poll",
        )
        self.scheduler.add_job(
            NidoDaemonService.log_data,
            args=[self.MQTTclient],
            trigger="interval",
            seconds=MQTTConfig.POLL_INTERVAL,
            name="DataLogger",
        )

        self.RPCserver = ThreadedServer(
            NidoDaemonService(self.scheduler),
            port=int(os.environ["NIDOD_RPC_PORT"]),
            protocol_config={"allow_public_attrs": True, "allow_pickle": True},
        )

        self.MQTTclient.loop_start()
        self.scheduler.start()
        self.RPCserver.start()  # Blocking

    def quit(self):
        self.controller.shutdown()
        self.RPCserver.close()
        self.scheduler.shutdown()
        self.MQTTclient.disconnect()
        self._l.info("Nido daemon shutdown")
        self._l.info("********************")
        return


if __name__ == "__main__":
    pid_file = os.environ["NIDOD_PID_FILE"]
    work_dir = os.environ["NIDOD_WORK_DIR"]
    log_file = os.environ["NIDOD_LOG_FILE"]

    handler = logging.handlers.TimedRotatingFileHandler(
        log_file, when="midnight", backupCount=7
    )
    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(name)s | %(message)s",
        datefmt="%d/%m/%Y %H:%M:%S",
    )
    handler.setFormatter(formatter)
    root = logging.getLogger()
    if "NIDO_DEBUG" in os.environ:
        root.setLevel(logging.DEBUG)
    else:
        root.setLevel(logging.INFO)
    root.addHandler(handler)

    daemon = NidoDaemon(pid_file, work_dir, stderr=log_file, stdout=log_file)

    if "start" == sys.argv[1]:
        daemon.start()
    elif "stop" == sys.argv[1]:
        daemon.stop()
    elif "restart" == sys.argv[1]:
        daemon.restart()
