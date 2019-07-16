FROM python:3.5-alpine AS nido-base

RUN apk add tzdata \
    && cp /usr/share/zoneinfo/America/Los_Angeles /etc/localtime \
    && echo "America/Los_Angeles" > /etc/timezone \
    && apk del tzdata


RUN pip install pip wheel setuptools --upgrade

COPY ./nido-lib /nido-lib
WORKDIR /nido-lib

RUN pip wheel --wheel-dir=/wheelhouse -r requirements.txt



FROM nido-base AS nido-api

COPY ./nido-api /app
WORKDIR /app

VOLUME /app/instance

RUN pip install -r requirements.txt --find-links /wheelhouse

ENV NIDOD_RPC_HOST nido-supervisor
ENV NIDOD_RPC_PORT 49152

EXPOSE 80

ENTRYPOINT ["gunicorn", "-b 0.0.0.0:80", "nido:create_app()"]



FROM nido-base AS nido-supervisor

COPY ./nido-supervisor /app
WORKDIR /app

RUN pip3 install -r requirements.txt --find-links /wheelhouse

ENV NIDO_BASE=/app
ENV NIDO_TESTING_GPIO=/tmp/gpio_pins.yaml
ENV NIDO_TESTING=""
ENV NIDOD_LOG_FILE=/app/log/nidod.log
ENV NIDOD_RPC_PORT=49152
ENV NIDOD_MQTT_CLIENT_NAME=Nido
ENV NIDOD_MQTT_HOSTNAME=mosquitto
ENV NIDOD_MQTT_PORT=1883

VOLUME /app/instance
VOLUME /app/log

EXPOSE 49152

ENTRYPOINT ["python3", "-m", "nidod.supervisor"]
