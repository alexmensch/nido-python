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

from datetime import datetime
import logging

from nido.supervisor.hardware import Sensor, Controller
from nido.supervisor.config import MQTTConfig
from nido.supervisor import db


class DataLogger(object):
    def __init__(self):
        self._l = logging.getLogger(__name__)
        return None

    def _get_sensor_data(self):
        return Sensor().get_conditions()["conditions"]

    def _get_controller_state(self):
        return Controller().get_status()

    def _get_thermostat_settings(self):
        return db.get_settings()

    def get_data(self):
        data = {}
        sensor_data = self._get_sensor_data()
        settings = self._get_thermostat_settings()

        unixtime = datetime.now().timestamp()
        data["controller"] = self._get_controller_state()
        data.update(sensor_data)
        data["set_temp"] = settings["set_temp"]
        return (unixtime, data)

    @staticmethod
    def format_influx(measurement, data, time):
        nanoseconds = int(time * 1000000000)
        line_protocol = "thermostat {}={} {}".format(measurement, data, nanoseconds)
        return line_protocol


class MQTTDataLogger(DataLogger):
    def __init__(self, client):
        super().__init__()
        self.client = client
        self.client.on_publish = self._on_publish

    def publish_data(self):
        (unixtime, data) = self.get_data()
        for measurement in data:
            payload = self.format_influx(measurement, data[measurement], unixtime)
            self._l.debug("payload: {}".format(payload))
            self.client.publish(
                "{}{}".format(MQTTConfig.TOPIC_BASE, measurement),
                payload=payload,
                qos=2,
            )
        return None

    def _on_publish(self, client, userdata, mid):
        pass
