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

from builtins import object

import os


class FlaskConfig(object):
    ENV = "production"
    DEBUG = False
    TESTING = False
    RPC_HOST = os.environ["NIDOD_RPC_HOST"]
    RPC_PORT = int(os.environ["NIDOD_RPC_PORT"])


class DevelopmentConfig(FlaskConfig):
    ENV = "development"
    DEBUG = True


class ProductionConfig(FlaskConfig):
    pass
