#!/bin/bash

# Debug mode
set -x

# Search and replace terms and paths
DEV="dev"
PROD="prod"
DEV_PATH="./${DEV}"
PROD_PATH="./${PROD}"

# rsync /dev/ to /prod
rsync -az --delete ${DEV_PATH}/ ${PROD_PATH}

# Search and replace to update paths
sed -i "s/${DEV}/${PROD}/g" ${PROD_PATH}/config.py
sed -i "s/${DEV}/${PROD}/g" ${PROD_PATH}/cfg/config.yaml
