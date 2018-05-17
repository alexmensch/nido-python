#!/bin/bash

sil=""
debug=""
testing=""
python3=""
py_ver="python"
usage() { echo "Usage: $0 -b <base path> [-s] [-d] [-t] [-3]" 1>&2; exit 1; }

while getopts ":b:sdt3" opt; do
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
        3)
            python3=true
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

if [ "${python3}" = true ]; then
    py_ver="python3"
fi

export NIDO_BASE=${base}
sudo -E ${py_ver} ${base}/app/nidod.py start
sudo -E bash -c "${py_ver} ${base}/app/nido.py ${sil}"
