#!/bin/bash

openssl req -x509 -newkey rsa:4096 -nodes -out instance/nido_cert.pem -keyout instance/nido_key.pem -days 365
