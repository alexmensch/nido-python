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

import os

from nido.lib import Mode


class SchedulerConfig(object):
    POLL_INTERVAL = 300


class DaemonConfig(object):
    DB_PATH = "{}/instance/nido.sqlite".format(os.environ["NIDO_BASE"])


class HardwareConfig(object):
    GPIO_COOL_PIN = 20
    GPIO_HEAT_PIN = 26
    HYSTERESIS = 0.6
    MODES = [Mode.Off.name, Mode.Heat.name]


class MQTTConfig(object):
    if "NIDOD_MQTT_HOSTNAME" in os.environ:
        HOSTNAME = os.environ["NIDOD_MQTT_HOSTNAME"]
    else:
        HOSTNAME = None
    PORT = os.environ["NIDOD_MQTT_PORT"]
    KEEPALIVE = 60
    CLIENT_NAME = os.environ["NIDOD_MQTT_CLIENT_NAME"]
    TOPIC_BASE = "nido/"
    POLL_INTERVAL = 60
