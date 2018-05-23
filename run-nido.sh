#!/bin/bash

# With gunicorn:
# $ sudo -E gunicorn -w 1 -b 0.0.0.0:80 'nido:create_app()'

# Using .env at the moment, but should export ENV variables in this script for debug

sil=""
debug=""
testing=""
python2=""
py_ver="python3"
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
            ;;
        t)
            testing=true
            ;;
        2)
            python2=true
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

if [ "${debug}" = true ]; then
    export NIDO_DEBUG=""
fi

if [ "${testing}" = true ]; then
    export NIDO_TESTING=""
    export NIDO_TESTING_GPIO="/tmp/gpio_pins.yaml"
fi

if [ "${python2}" = true ]; then
    py_ver="python"
fi

export NIDO_BASE=${base}
sudo -E ${py_ver} ${base}/app/nidod.py start
sudo -E bash -c "${py_ver} ${base}/app/nido.py ${sil}"
