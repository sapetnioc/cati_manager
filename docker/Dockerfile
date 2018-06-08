FROM ubuntu:16.04

ARG LDAP_PASSWORD="ldap_password"
ARG DOMAIN_NAME="cati_manager.cati-neuroimaging.com"
ARG ORGANIZATION="cati"
ARG LDAP_BASE="dc=cati_manager,dc=cati-neuroimaging,dc=com"

ARG USER_ACCOUNT=cati_manager
ARG USER_PASSWORD=openbar

EXPOSE 8080

RUN apt-get update 
RUN apt-get upgrade -y
RUN DEBIAN_FRONTEND=noninteractive apt-get install --fix-missing -y \
    gosu \
    slapd \
    ldap-utils \
    libpam-ldap \
    nscd \
    phpldapadmin \
#     patch \
    python-apt \
    python-pip \
#     mercurial \
#     gcc \
    libldap2-dev \
    libsasl2-dev \
    libssl-dev \
#     libxml2-dev \
#     libxslt1-dev \
#     libpq-dev \
#     libgecode-dev \
    postgresql \
    postgresql-plpython-9.5 \
    python3-pip \
    python3-dev \
    python3-virtualenv \
    pgadmin3 \
    gettext \
    libffi-dev
    vim \
    git

# LDAP configuration
RUN echo -e '# Omit OpenLDAP server configuration?\n\
slapd	slapd/no_configuration	boolean	false\n\
# DNS domain name:\n\
slapd	slapd/domain	string	'$DOMAIN_NAME'\n\
# Organization name:\n\
slapd	shared/organization	string	'$ORGANIZATION'\n\
# Administrator password:\n\
slapd	slapd/password1	password	'$LDAP_PASSWORD'\n\
# Confirm password:\n\
slapd	slapd/password2	password	'$LDAP_PASSWORD'\n\
# Database backend to use:\n\
# Choices: BDB, HDB, MDB\n\
slapd	slapd/backend	select	MDB\n\
# Do you want the database to be removed when slapd is purged?\n\
slapd	slapd/purge_database	boolean	true\n\
# Move old database?\n\
slapd	slapd/move_old_database	boolean	true\n\
# Allow LDAPv2 protocol?\n\
slapd	slapd/allow_ldap_v2	boolean	false\n\
' | debconf-set-selections && \
DEBIAN_FRONTEND=noninteractive dpkg-reconfigure slapd -fnoninteractive

# PHPLDAPadmin configuration
RUN echo -e "161c161\n\
< // \$config->custom->appearance['hide_template_warning'] = false;\n\
---\n\
> // \$config->custom->appearance['hide_template_warning'] = true;\n\
300c300\n\
< \$servers->setValue('server','base',array('dc=example,dc=com'));\n\
---\n\
> \$servers->setValue('server','base',array('$LDAP_BASE'));\n\
326c326\n\
< \$servers->setValue('login','bind_id','cn=admin,dc=example,dc=com');\n\
---\n\
> \$servers->setValue('login','bind_id','cn=admin,$LDAP_BASE');\n\
"| patch  /etc/phpldapadmin/config.php -


# RUN groupadd $USER_ACCOUNT && useradd -g $USER_ACCOUNT -p "$USER_PASSWORD" -ms /bin/bash $USER_ACCOUNT
# COPY data/cw_required /tmp/cw_required

RUN locale-gen en_US.UTF-8
COPY postgresql_force_utf8_template.sql /tmp
RUN gosu postgres service postgresql start && \
    gosu postgres createuser --superuser $USER_ACCOUNT && \
    gosu postgres psql -f /tmp/postgresql_force_utf8_template.sql && \
# #     mkdir /etc/publication && \
# #     echo '{"ldap-password": "'$LDAP_PASSWORD'","base-dn": "'$LDAP_BASE'"}' > /etc/publication/ldap_configuration.json && \
# #     chown $USER_ACCOUNT:$USER_ACCOUNT etc/publication/ldap_configuration.json  && \
# #     gosu $USER_ACCOUNT /tmp/install_cube_instance &&
    gosu postgres service postgresql stop

    
# RUN < /dev/urandom tr -dc _A-Z-a-z-0-9 | head -c${1:-32} > /etc/publication/secret-key && \
#     chown $USER_ACCOUNT:$USER_ACCOUNT etc/publication/secret-key
