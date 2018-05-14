#!/bin/bash

sil=""
debug=""
testing=""
usage() { echo "Usage: $0 -b <base path> [-s] [-d] [-t]" 1>&2; exit 1; }

while getopts ":b:sdt" opt; do
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

export NIDO_BASE=${base}
sudo -E python ${base}/app/nidod.py start
sudo -E bash -c "python ${base}/app/nido.py ${sil}"
