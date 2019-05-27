FROM postgres:alpine

COPY install.sh /docker-entrypoint-initdb.d/install.sh
COPY postgresql.conf /tmp/postgresql.conf
RUN chown postgres:postgres /tmp/postgresql.conf && chmod u=rw,g=,o= /tmp/postgresql.conf

ENV PGDATA /cati_portal/postgres
ENV POSTGRES_PASSWORD_FILE /cati_portal/run/postgres_secret
