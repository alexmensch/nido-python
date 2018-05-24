#!/bin/bash

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
    export FLASK_RUN_SERVER="${server}"
    export FLASK_RUN_PORT="${port}"
    export FLASK_ENV="development"
    export FLASK_DEBUG="TRUE"
    cd ${base} && sudo -E ${py_ver} nido/nidod.py start && sudo -E flask run --without-threads
fi
