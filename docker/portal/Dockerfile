FROM ubuntu:18.04

RUN apt-get update && \
    apt-get -y install \
        curl \
        git \
        gnupg2 python3-wheel \
        ipython3 \
        python3-click \
        python3-flask \
        python3-flask-login \
        python3-venv \
        python3-waitress \
        python3-psycopg2 \
        python3-pgpy \
        python3-yaml && \
    apt-get autoremove && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN mkdir /cati_portal
ENV CATI_PORTAL_DIR="/cati_portal"

RUN python3 -m venv --system-site-packages "$CATI_PORTAL_DIR/venv"

ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8
ENV FLASK_APP=cati_portal.wsgi
