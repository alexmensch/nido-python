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

import logging
import logging.handlers
import os
import signal
import sys
import time

import paho.mqtt.client as mqtt
from rpyc.utils.server import ThreadedServer
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from nido.lib.rpc.server import NidoDaemonService
from nido.lib import Status
from nido.supervisor.config import SchedulerConfig, DaemonConfig, MQTTConfig
from nido.supervisor.hardware import Controller
from nido.supervisor import db


class Supervisor(object):
    def __init__(self):
        self._l = logging.getLogger()
        self.controller = Controller()
        self.scheduler = BackgroundScheduler()
        return None

    def run(self):
        self._l.debug("Starting Nido supervisor...")

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

        if MQTTConfig.HOSTNAME:
            self.MQTTclient = mqtt.Client(MQTTConfig.CLIENT_NAME, clean_session=False)
            self.MQTTclient.enable_logger()
            self.MQTTclient.connect_async(
                MQTTConfig.HOSTNAME,
                port=int(MQTTConfig.PORT),
                keepalive=MQTTConfig.KEEPALIVE,
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
            protocol_config={
                "allow_pickle": True,
                "allow_all_attrs": True,
                "instantiate_custom_exceptions": True,
            },
        )

        signal.signal(signal.SIGTERM, self.shutdown_handler)
        signal.signal(signal.SIGINT, self.shutdown_handler)

        if MQTTConfig.HOSTNAME:
            self.MQTTclient.loop_start()
        self.scheduler.start()
        self.RPCserver.start()  # Blocking
        return None

    def shutdown_handler(self, sig, frame):
        self._l.info("Received signal {}, shutting down...".format(sig))
        self.shutdown()
        sys.exit(0)

    def shutdown(self):
        self.controller.shutdown()
        self.RPCserver.close()
        self.scheduler.shutdown()
        if MQTTConfig.HOSTNAME:
            self.MQTTclient.disconnect()
        while self.controller.get_status() is not Status.Off.value:
            supervisor._l.critical("Hardware not shutdown. Retrying...")
            self.controller.shutdown()
            time.sleep(1)
        supervisor._l.info("Shutdown complete")
        supervisor._l.info("*****************")
        return None


if __name__ == "__main__":
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

    if not os.path.exists(DaemonConfig.DB_PATH):
        db._init_db()

    supervisor = Supervisor()
    supervisor.run()
