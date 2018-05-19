#!/bin/bash

python2=""
py_ver="python3"
usage() { echo "Usage: $0 -b <base path> [-2]" 1>&2; exit 1; }

while getopts ":b:2" opt; do
    case "${opt}" in
        b)
            base=${OPTARG}
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

if [ "${python2}" = true ]; then
    py_ver="python"
fi

export NIDO_BASE=${base}
sudo -E ${py_ver} ${base}/app/nidod.py stop
