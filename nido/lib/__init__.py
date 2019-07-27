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

from enum import Enum


class Mode(Enum):
    Off = 0
    Heat = 1
    Cool = 2
    Heat_Cool = 3


class Status(Enum):
    Off = 0
    Heating = 1
    Cooling = 2


def c_to_f(c):
    f = (float(c) * 9 / 5) + 32
    f = round(f * 10) / 10
    f = float("{0:.1f}".format(f))
    return f


def f_to_c(f):
    c = (float(f) - 32) * 5 / 9
    c = round(c * 10) / 10
    c = float("{0:.1f}".format(c))
    return c
