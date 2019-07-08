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

echo "Creating local adhoc SSL certificates..."
echo
openssl req -x509 -newkey rsa:4096 -nodes -out instance/nido_cert.pem -keyout instance/nido_key.pem -days 365

echo "Installing required packages..."
echo
pip install -r requirements.txt --no-index --find-links wheelhouse

echo "Initializing daemon database..."
echo
export NIDOD_PID_FILE=""
export NIDOD_MQTT_HOSTNAME=""
export NIDOD_MQTT_PORT=""
export NIDOD_MQTT_CLIENT_NAME=""
python nidod/db.py

echo "Setting up npm..."
echo
npm install
npm run build-prod

echo
echo "********"
echo "To complete installation you must create:"
echo " instance/private-config.py"
echo "********"
echo

