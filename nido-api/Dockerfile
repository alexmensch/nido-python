FROM python:3-alpine

COPY . /app
WORKDIR /app

RUN pip install -r requirements.txt

ENV NIDOD_RPC_HOST nido-daemon
ENV NIDOD_RPC_PORT 49152

ENTRYPOINT ["gunicorn", "-b 0.0.0.0:80", "nido:create_app()"]
