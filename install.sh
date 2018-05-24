#!/bin/bash
python3 -m venv venv && source venv/bin/activate
pip install --upgrade pip
npm install
npm run build-prod
mkdir instance
openssl req -x509 -newkey rsa:4096 -nodes -out instance/nido_cert.pem -keyout instance/nido_key.pem -days 365
