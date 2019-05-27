FROM debian

ENV DEBIAN_FRONTEND noninteractive
RUN apt-get update && apt-get -y install libnss-ldapd libpam-ldapd openssh-sftp-server openssh-server
RUN apt-get update && apt-get -y install rsyslog
RUN mkdir -p /var/run/sshd
ADD entrypoint.sh /entrypoint.sh
RUN chmod u+x /entrypoint.sh

CMD /entrypoint.sh
