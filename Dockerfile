FROM raspbian/stretch AS base

RUN apt-get update && apt-get install -y \
    -o APT::Install-Recommends=false \
    -o APT::Install-Suggests=false \
    python3 \
 && rm -rf /var/lib/apt/lists/*

ENV VIRTUAL_ENV=/venv
ENV NIDO_BASE=/app


FROM base AS builder

RUN apt-get update && apt-get install -y \
    -o APT::Install-Recommends=false \
    -o APT::Install-Suggests=false \
    python3-pip \
    python3-venv

RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

RUN pip install pip wheel setuptools --upgrade

COPY . $NIDO_BASE
WORKDIR $NIDO_BASE

RUN python setup.py package


FROM base

ENV PATH="$VIRTUAL_ENV/bin:$PATH"

COPY --from=builder $VIRTUAL_ENV $VIRTUAL_ENV
COPY --from=builder $NIDO_BASE/dist/nido*.tar.gz $NIDO_BASE/

WORKDIR $NIDO_BASE
VOLUME $NIDO_BASE/instance
VOLUME /var/log

RUN tar -xpvf $NIDO_BASE/nido*.tar.gz -C $NIDO_BASE --strip-components=1
RUN pip install -r requirements.txt --no-index --find-links wheelhouse
