#!/bin/bash

sil=""
debug=""
usage() { echo "Usage: $0 -b <base path> [-s] [-d]" 1>&2; exit 1; }

while getopts ":b:sd" opt; do
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

export NIDO_BASE=${base}
sudo -E python ${base}/app/nidod.py start
sudo -E bash -c "python ${base}/app/nido.py ${sil}"
