#!/bin/bash

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
