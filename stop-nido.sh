#!/bin/bash

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

python2=""
py_ver="python3"
usage() { echo "Usage: $0 -b <base path> [-t] [-2]" 1>&2; exit 1; }

while getopts ":b:t2" opt; do
    case "${opt}" in
        b)
            base=${OPTARG}
            ;;
        t)
            export NIDO_TESTING=""
            export NIDO_TESTING_GPIO="/tmp/gpio_pins.yaml"
            ;;
        2)
            py_ver="python"
            ;;
        *)
            usage
            ;;
    esac
done
shift $((OPTIND-1))

if [ -z "${base}" ]; then
    usage
fi

export NIDO_BASE=${base}
sudo -E ${py_ver} ${base}/nido/nidod.py stop
