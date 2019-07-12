FROM raspbian/stretch AS lib-builder

RUN apt-get update && apt-get install -y \
    -o APT::Install-Recommends=false \
    -o APT::Install-Suggests=false \
    python3 \
    python3-pip \
 && rm -rf /var/lib/apt/lists/*

RUN pip3 install pip wheel setuptools --upgrade

COPY ./nido-lib /nido-lib
WORKDIR /nido-lib

RUN pip3 wheel --wheel-dir=wheelhouse -r requirements.txt


FROM python:3.5-alpine AS nido-api

VOLUME /app/instance
COPY ./nido-api /app
COPY --from=lib-builder /nido-lib/wheelhouse /wheelhouse

WORKDIR /app

RUN pip install -r requirements.txt --find-links /wheelhouse

ENV NIDOD_RPC_HOST nido-daemon
ENV NIDOD_RPC_PORT 49152

EXPOSE 80

ENTRYPOINT ["gunicorn", "-b 0.0.0.0:80", "nido:create_app()"]


FROM python:3.5-alpine AS nido-daemon

VOLUME /app/instance
VOLUME /app/log
COPY ./nido-daemon /app
COPY --from=lib-builder /nido-lib/wheelhouse /wheelhouse

WORKDIR /app

RUN pip install -r requirements.txt --find-links /wheelhouse

ENV NIDO_BASE /app
ENV NIDOD_PID_FILE /tmp/nido.pid
ENV NIDOD_WORK_DIR /tmp
ENV NIDOD_LOG_FILE /app/log/nidod.log
ENV NIDOD_MQTT_CLIENT_NAME Nido
ENV NIDOD_MQTT_HOSTNAME mqtt
ENV NIDOD_MQTT_PORT 1883

EXPOSE 49152

ENTRYPOINT ["python", "daemon.py", "start"]


FROM eclipse-mqtt AS mqtt

COPY ./mqtt/mosquitto.conf /mosquitto/config/mosquitto.conf

