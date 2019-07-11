FROM python:3.5-alpine

COPY . /app
WORKDIR /app

RUN pip install -r requirements.txt

ENV NIDOD_RPC_HOST nido-daemon
ENV NIDOD_RPC_PORT 49152

EXPOSE 80

ENTRYPOINT ["gunicorn", "-b 0.0.0.0:80", "nido:create_app()"]
