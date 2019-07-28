FROM python:3.7-alpine AS nido-base

RUN apk add tzdata \
    && cp /usr/share/zoneinfo/America/Los_Angeles /etc/localtime \
    && echo "America/Los_Angeles" > /etc/timezone \
    && apk del tzdata

RUN pip install pip wheel setuptools --upgrade

COPY . /app/
WORKDIR /app

RUN pip install -r requirements.txt

VOLUME /app/nido
VOLUME /app/instance
VOLUME /app/log



FROM nido-base AS nido-api

COPY private-config.py /app/instance/

ENV NIDOD_RPC_PORT=49152

EXPOSE 80

ENTRYPOINT ["gunicorn", "-b 0.0.0.0:80", "nido.web:create_app()"]



FROM nido-base AS nido-supervisor

ENV NIDO_BASE=/app \
    NIDOD_LOG_FILE=/app/log/nidod.log \
    NIDOD_RPC_PORT=49152 \
    NIDOD_MQTT_CLIENT_NAME=Nido \
    NIDOD_MQTT_PORT=1883

ENTRYPOINT ["python", "-m", "nido.supervisor"]
