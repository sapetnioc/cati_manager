'''
To install catidb_manager, TODO
'''
import argparse

import sys
import os.path as osp
import configparser
from getpass import getpass
import hashlib

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

parser = argparse.ArgumentParser()
parser.add_argument('config_file', help='*.ini file containing cati_manager application settings')
parser.add_argument('--erase-database-and-roles', help='Drop (i.e. delete) the database defined in the configuration file as well as all roles (i.e. users and groups) whose name contains a $ sign', action='store_true')
parser.add_argument('-d', '--data', help='Insert test data into database', action='store_true')
options = parser.parse_args()

config = configparser.ConfigParser()
config.read(options.config_file)

missing_settings = []
postgresql_host = config['app:main'].get('cati_manager.postgresql_host')
postgresql_port = config['app:main'].get('cati_manager.postgresql_port')
if not postgresql_host:
    print('Postgresql connection settings are missing')
    missing_settings.append('''# Host name fo the PostgreSQL server
cati_manager.postgresql_host = localhost
# Port of the PostgreSQL server (optional)
; cati_manager.postgresql_port = 5432
''')
database_admin = config['app:main'].get('cati_manager.database_admin')
if not database_admin:
    print('Database admin name is missing')
    missing_settings.append('''# Name of a PostgreSQL superuser dedicated to cati_manager.
cati_manager.database_admin = cati_manager
''')
challenge = config['app:main'].get('cati_manager.database_admin_challenge')
if not challenge:
    print('Database admin password is missing')
    for i in range(3):
        pwd1 = getpass('Select a passord for database admin: ')
        pwd2 = getpass('Re-type the password: ')
        if pwd1 != pwd2:
            print('Both passwords are not equal, retry.')
        else:
            challenge = hashlib.sha256(pwd1.encode('utf-8')).hexdigest()
            missing_settings.append('''# Hash of the password selected for the database administrator.
# To generate a new hash given a password, one can use the following Python code:
# import hashlib, getpass
# pwd = getpass.getpass()
# challenge = hashlib.sha256(pwd.encode('utf-8')).hexdigest()
# print(challenge)
cati_manager.database_admin_challenge = %s
''' % challenge)
            break
    else:
        print('Too many password, mismatch. Installation canceled.')
        sys.exit(1)
database = config['app:main'].get('cati_manager.database')
if not database:
    print('Database name missing')
    missing_settings.append('''# Name of the PostgreSQL database dedicated to cati_manager.
cati_manager.database = cati_manager
''')
maintenance_path = config['app:main'].get('cati_manager.maintenance_path')
if not maintenance_path:
    print('Maintenance path missing')
    missing_settings.append('''# Name of the JSON file used to store temporary maintenance information
cati_manager.maintenance_path = ~/.config/cati/cati_manager_maintenance.json
''')
if missing_settings:
    print('\nAdd the following settings to the [app:main] section of %s:\n' % options.config_file)
    print('\n'.join(missing_settings))
    sys.exit(1)

# Try to connect to postgres database. We use this database because the 
# cati_manager database may not exists yet and we want to check
# PostgreSQL connection settings.
try:
    dbm = psycopg2.connect(database='postgres', host=postgresql_host, port=postgresql_port, user=database_admin, password=challenge)
except psycopg2.OperationalError as error:
    # Check if error is due to authentication failure
    # I wish I know a better way to know the cause of a connection error
    if 'password authentication' in str(error):
        dbm = None
    else:
        raise

if not dbm:
    print('''PostgreSQL authentication failed for {0}
If {0} superuser is not created in PostgreSQL, you can use psql to create it :
  sudo -u postgres psql -n
  CREATE ROLE {0} WITH SUPERUSER LOGIN PASSWORD '{1}';'''.format(database_admin, challenge))
    sys.exit(1)

# Try to connect to cati_manager database
try:
    db = psycopg2.connect(database=database, host=postgresql_host, port=postgresql_port, user=database_admin, password=challenge)
except psycopg2.OperationalError as error:
    # Check if error is due to non exisiting database
    # I wish I know a better way to know the cause of a connection error
    if 'does not exist' in str(error):
        db = None
    else:
        raise

if options.erase_database_and_roles:
    if db:
        print('Deleting database', database)
        db = None
        dbm.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        dbm.cursor().execute('DROP DATABASE %s;' % database)
    with dbm.cursor() as cur:
        cur.execute('SELECT rolname FROM pg_catalog.pg_roles;')
        for row in cur.fetchall():
            role = row[0]
            if '$' in role:
                print('Delete role', role)
                cur.execute('DROP ROLE %s;' % role)
if db is None:
    print('Creating database', database)
    dbm.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    dbm.cursor().execute('CREATE DATABASE %s;' % database)

# Close connection on postgres database
dbm = None
# Connect to cati_manager database
db = psycopg2.connect(database=database, host=postgresql_host, port=postgresql_port, user=database_admin, password=challenge)

# Check if catidb_manager schema exists in database
cur = db.cursor()
cur.execute("SELECT COUNT(*) FROM information_schema.schemata WHERE schema_name = 'cati_manager'")
if not cur.fetchone()[0]:
    with db:
        with cur:
            print('Database initialization')
            f, e = osp.splitext(__file__)
            sql = open(f + '.sql').read()
            cur.execute(sql)
            if options.data:
                print('Add test data')
                sql = open(f + '_test_data.sql').read()
                cur.execute(sql)
