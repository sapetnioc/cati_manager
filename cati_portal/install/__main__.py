'''
This script is called by the command "cati_portal_ctl install" after the
creation of singularity images and venv where cati_portal is
installed ; it is executed in the container and using venv to install a
cati_portal instance.
'''

import subprocess
import os
import os.path as osp
import sys
import tempfile
import secrets
import shutil

import pgpy
import psycopg2

from cati_portal.migration import sql_changesets
from cati_portal.encryption import (pgp_public_key, generate_password,
                                    hash_password)


def install(delete_existing, pg_port, http_port):
    # This function must be called from within a container where the base
    # directory is always in /cati_portal
    directory = '/cati_portal'
    venv = osp.join(directory, 'venv')
    log = osp.join(directory, 'log')
    run = osp.join(directory, 'run')
    tmp = osp.join(directory, 'tmp')
    pgp = osp.join(directory, 'pgp')
    instance = osp.join(directory, 'flask_instance')
    postgresql = osp.join(directory, 'postgresql')
    hash_file = osp.join(tmp, 'installation.hash')

    if delete_existing:
        for path in (postgresql, log, run, tmp, instance, hash_file):
            if osp.exists(path):
                print('Delete', path)
                if osp.isdir(path):
                    shutil.rmtree(path)
                else:
                    os.remove(path)

    if not osp.exists(tmp):
        os.mkdir(tmp)

    if not osp.exists(log):
        os.mkdir(log)

    if not osp.exists(run):
        os.mkdir(run)

    if not osp.exists(pgp):
        os.mkdir(pgp)
        pgp_tmp = tempfile.mkdtemp(prefix='pgp.', dir=tmp)
        try:
            c_pgp_tmp = osp.join('/cati_portal/tmp', osp.basename(pgp_tmp))
            pgp_script = '''%echo Generating cati_portal PGP key
%no-protection
Key-Type: 1
Subkey-Type: default
Name-Real: cati_portal
Name-Comment: no comment
Name-Email: cati_portal@cati-neuroimaging.com
Expire-Date: 0
%commit
%echo done
'''
            subprocess.run(['gpg2', '--batch', '--gen-key', '--homedir', c_pgp_tmp], input=pgp_script.encode('UTF8'), check=True)
            subprocess.run(['gpg2', '--list-keys', '--homedir', c_pgp_tmp], check=True)
            public_key = subprocess.check_output(['gpg2', '--homedir', c_pgp_tmp, '--export', 'cati_portal'])
            public_key_file = osp.join(pgp, 'public.key')
            open(public_key_file, 'wb').write(public_key)
            key, other = pgpy.PGPKey.from_file(public_key_file)
            secret_key = subprocess.check_output(['gpg2', '--homedir', c_pgp_tmp, '--export-secret-keys', 'cati_portal'])
            open(osp.join(pgp, 'secret.key'), 'wb').write(secret_key)
        finally:
            shutil.rmtree(pgp_tmp, ignore_errors=True)

    if not osp.exists(postgresql):
        subprocess.run(['pg_ctl', 'initdb'], check=True)

        conf_file = osp.join(postgresql, 'postgresql.conf')
        conf = open(conf_file).read()
        for f, r in (("#port = 5432", 'port = %s' % pg_port),
                     ("#unix_socket_directories = '/var/run/postgresql'", "unix_socket_directories = '%s'" % run)):
            new_conf = conf.replace(f, r)
            if new_conf == conf:
                raise ValueError('Cannot find "%s" in %s' % (f, conf_file))
            conf = new_conf
        open(conf_file, 'w').write(conf)

        conf_file = osp.join(postgresql, 'pg_hba.conf')
        print('''local   all             all                                     peer
host    all             all             127.0.0.1/32            md5
''', file=open(conf_file, 'w'))

        pg_password = secrets.token_urlsafe()
        # Start postgresql
        subprocess.run(['pg_ctl', '-l', osp.join(log, 'postgresql.log'), 'start'], check=True)
        try:
            subprocess.run(['createdb', '-p', pg_port, 'cati_portal'], check=True)
            with psycopg2.connect(dbname='cati_portal', port=pg_port) as db:
                with db.cursor() as cur:
                    cur.execute("CREATE ROLE cati_portal NOINHERIT BYPASSRLS LOGIN PASSWORD '%s'" % pg_password)
                    for id, sql in sql_changesets('cati_portal.db'):
                        cur.execute(sql)

                    sql = "INSERT INTO cati_portal.pgp_public_keys (name, pgp_key) VALUES ('cati_portal', %s);"
                    cur.execute(sql, [bytes(pgp_public_key())])
        finally:
            subprocess.run(['pg_ctl', 'stop'], check=True)

    if not osp.exists(instance):
        os.mkdir(instance)
        config_file = osp.join(instance, 'config.json')
        print('''{
    "POSTGRES_HOST": "localhost",
    "POSTGRES_PORT": "%s",
    "POSTGRES_USER": "cati_portal",
    "POSTGRES_PASSWORD": "%s",
    "POSTGRES_DATABASE": "cati_portal",
    "HTTP_PORT": "%s",
    "WORKERS_COUNT": 4
}
''' % (pg_port, pg_password, http_port), file=open(config_file, 'w'))

    # Create an installation password and store its hash representation
    installation_password = generate_password(16)
    open(hash_file, 'wb').write(hash_password(installation_password))
    print('Installation password =', installation_password)


delete_existing = sys.argv[1] == 'True'
pg_port = sys.argv[2]
http_port = sys.argv[3]

install(delete_existing, pg_port, http_port)
