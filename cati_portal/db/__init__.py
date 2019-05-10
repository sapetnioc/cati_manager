import collections
import threading
import time

from flask import current_app, g
from flask_login import current_user
import pgpy
import psycopg2

from cati_portal.encryption import pgp_secret_key


class ConnectionPool:
    class ConnectionRecord:
        def __init__(self, user_id, creation_time, last_used, connection):
            self.user_id = user_id
            self.creation_time = creation_time
            self.last_used = last_used
            self.connection = connection

    def __init__(self, max_connections=6):
        self.lock = threading.RLock()
        self.max_connections = max_connections
        self.free = collections.deque()
        self.in_use = collections.deque()

    def get_connection(self, user_id):
        with self.lock:
            if self.free:
                record = self.free.popleft()
                record.last_used = time.time()
                self.in_use.append(record)
                return record.connection
            if len(self.in_use) == self.max_connections:
                raise RuntimeError('All database connections are in use')
            connection =  psycopg2.connect(host=current_app.config['POSTGRES_HOST'],
                                           port=current_app.config['POSTGRES_PORT'],
                                           dbname=current_app.config['POSTGRES_DATABASE'],
                                           user=current_app.config['POSTGRES_USER'],
                                           password=current_app.config['POSTGRES_PASSWORD'])
            if user_id is not None:
                pg_user = 'cati_portal$' + user_id
                with connection.cursor() as cur:
                    cur.execute('SET ROLE %s;' % pg_user)
            record = self.ConnectionRecord(user_id=user_id,
                                           creation_time=time.time(),
                                           last_used=time.time(),
                                           connection=connection)
            self.in_use.append(record)
            return record.connection

    def free_connection(self, connection):
        with self.lock:
            with connection.cursor() as cur:
                cur.execute('RESET ROLE;')
            for record in self.in_use:
                if record.connection == connection:
                    break
            else:
                record = None
            if record is not None:
                self.in_use.remove(record)
                record.last_used = time.time()
                self.free.append(record)


class WithDatabaseConnection:
    def __init__(self, login):
        self.login = login

    def __enter__(self):
        self.connection = current_app.db_pool.get_connection(self.login)
        return self.connection

    def __exit__(self, x, y, z):
        if x is None:
            self.connection.commit()
        else:
            self.connection.rollback()
        current_app.db_pool.free_connection(self.connection)
        self.connection = None


class WithDatabaseCursor:
    def __init__(self, login):
        self.login = login

    def __enter__(self):
        self.wdb = WithDatabaseConnection(self.login)
        connection = self.wdb.__enter__()
        self.cursor = connection.cursor()
        return self.cursor.__enter__()

    def __exit__(self, x, y, z):
        self.cursor.__exit__(x, y, z)
        self.wdb.__exit__(x, y, z)
        self.wdb = self.cursor = None


def get_db():
    '''
    with get_db() as db:
        with db.cursor() as cur:
            cur.execute(...)
    '''
    if current_user.is_authenticated and current_user.is_active:
        return WithDatabaseConnection(current_user.get_id())
    else:
        raise RuntimeError('insuficient rights to connect to the database')


def get_cursor():
    '''
    with get_admin_cursor() as cur:
        cur.execute(...)
    '''
    return WithDatabaseCursor(current_user.get_id())


def _get_admin_db():
    return WithDatabaseConnection(None)


def _get_admin_cursor():
    return WithDatabaseCursor(None)


def init_app(app):
    app.db_pool = ConnectionPool()
