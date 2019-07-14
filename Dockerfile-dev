FROM raspbian/stretch AS raspbian-base

RUN apt-get update && apt-get install -y \
    -o APT::Install-Recommends=false \
    -o APT::Install-Suggests=false \
    python3 \
    python3-pip \
 && rm -rf /var/lib/apt/lists/*

RUN pip3 install pip wheel setuptools --upgrade


FROM arm32v6/python:3.5-alpine AS nido-api

RUN pip install pip wheel setuptools --upgrade

COPY ./nido-lib /nido-lib
WORKDIR /nido-lib

RUN pip wheel --wheel-dir=/wheelhouse -r requirements.txt

COPY ./nido-api /app
WORKDIR /app

VOLUME /app/instance

RUN pip install -r requirements.txt --find-links /wheelhouse

ENV NIDOD_RPC_HOST nido-daemon
ENV NIDOD_RPC_PORT 49152

EXPOSE 80

ENTRYPOINT ["gunicorn", "-b 0.0.0.0:80", "nido:create_app()"]


FROM raspbian-base AS nido-daemon

COPY ./nido-lib /nido-lib
WORKDIR /nido-lib

RUN pip3 wheel --wheel-dir=/wheelhouse -r requirements.txt

COPY ./nido-daemon /app
WORKDIR /app

RUN pip3 install -r requirements.txt --find-links /wheelhouse

ENV NIDO_BASE /app
ENV NIDO_TESTING_GPIO=/tmp/gpio_pins.yaml
ENV NIDO_TESTING=""
ENV NIDOD_LOG_FILE /app/log/nidod.log
ENV NIDOD_RPC_PORT 49152
ENV NIDOD_MQTT_CLIENT_NAME Nido
ENV NIDOD_MQTT_HOSTNAME mosquitto
ENV NIDOD_MQTT_PORT 1883

VOLUME /app/instance
VOLUME /app/log

EXPOSE 49152

ENTRYPOINT ["python3", "-m", "nidod.supervisor"]


FROM arm32v6/eclipse-mosquitto AS nido-mqtt

COPY ./mqtt/mosquitto.conf /mosquitto/config/mosquitto.conf
