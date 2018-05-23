#!/bin/bash
npm install
npm run build-prod
flask init-db
pip install gunicorn
