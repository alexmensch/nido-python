#!/bin/bash
echo "Setting up python3 venv..."
python3 -m venv venv && source venv/bin/activate

echo "Creating local adhoc SSL certificates..."
mkdir instance
openssl req -x509 -newkey rsa:4096 -nodes -out instance/nido_cert.pem -keyout instance/nido_key.pem -days 365

pip install --upgrade pip
pip install -e .
pip install -r requirements.txt

npm install
npm run build-prod

echo
echo "********"
echo "To complete installation you must create:"
echo " instance/private-config.py"
echo " nido/cfg/config.yaml"
echo "********"
