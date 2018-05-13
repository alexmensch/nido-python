#!/bin/bash

sil=""
usage() { echo "Usage: $0 -b <base path> [-s]" 1>&2; exit 1; }

while getopts ":b:s" opt; do
    case "${opt}" in
        b)
            base=${OPTARG}
            ;;
        s)
            sil=">/dev/null 2>&1"
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

sudo -E python ${base}/app/nidod.py start
sudo -E bash -c "python ${base}/app/nido.py ${sil}"
