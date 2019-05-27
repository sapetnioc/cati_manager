FROM ubuntu:18.04

RUN apt-get update && \
    apt-get -y install \
        ipython3 \
        git \
        python3-click \
        python3-venv \
        gnupg2 python3-wheel \
        python3-waitress \
        python3-psycopg2 \
        python3-pgpy && \
    apt-get autoremove && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN mkdir /cati_portal
ENV CATI_PORTAL_DIR="/cati_portal"

RUN python3 -m venv --system-site-packages "$CATI_PORTAL_DIR/venv"


