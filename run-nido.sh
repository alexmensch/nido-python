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

sil=""
py_ver="python3"
server="0.0.0.0"
port="443"
debug=false
usage() { echo "Usage: $0 -b <base path> [-s] [-d] [-t] [-2]" 1>&2; exit 1; }

while getopts ":b:sdt2" opt; do
    case "${opt}" in
        b)
            base=${OPTARG}
            ;;
        s)
            sil=">/dev/null 2>&1"
            ;;
        d)
            debug=true
            server="127.0.0.1"
            port="80"
            export NIDO_DEBUG=""
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

if [ "${debug}" = false ]; then
    cd ${base} && sudo -E ${py_ver} nido/nidod.py start && sudo -E gunicorn -w 1 -b ${server}:${port} --certfile instance/nido_cert.pem --keyfile instance/nido_key.pem 'nido:create_app()'
else
    export FLASK_APP="nido"
    export FLASK_RUN_SERVER="${server}"
    export FLASK_RUN_PORT="${port}"
    export FLASK_ENV="development"
    export FLASK_DEBUG="TRUE"
    cd ${base} && sudo -E ${py_ver} nido/nidod.py start && sudo -E flask run --without-threads
fi
