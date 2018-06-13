FROM ubuntu:18.04

EXPOSE 80

RUN apt-get update 
RUN apt-get upgrade -y
RUN DEBIAN_FRONTEND=noninteractive apt-get install --fix-missing -y \
    python3-pip \
    python3-dev \
    python3-virtualenv \
    gettext \
    vim \
    nano \
    git

COPY . /src/cati_manager
RUN cd /src/cati_manager && pip3 install -e .

RUN echo '127.0.1.1	cati_manager.cati-neuroimaging.com' >> /etc/hosts

ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8

ENV FLASK_APP=cati_manager
ENV FLASK_ENV=development
ENV FLASK_DEBUG=1

ENV SERVER_NAME='cati_manager.cati-neuroimaging.com:80'

ENTRYPOINT ["flask"]
CMD ["run", "-h", "0.0.0.0", "-p", "80"]

