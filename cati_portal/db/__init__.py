import collections
import os
import pwd
import threading
import time

from flask import current_app, g
from flask_login import current_user
import pgpy
import psycopg2

from cati_portal.encryption import pgp_secret_key

class UserConnectionPool:
    class ConnectionRecord:
        def __init__(self, id, creation_time, last_used, connection):
            self.id = id
            self.creation_time = creation_time
            self.last_used = last_used
            self.connection = connection
    
    def __init__(self, max_connections=6):
        self.lock = threading.RLock()
        self.max_connections = max_connections
        self.free = collections.deque()
        self.in_use = collections.deque()
        
    def _get_connection(self, id, create_collection):
        with self.lock:
            for record in self.free:
                if record.id == id:
                    break
            else:
                record = None
            if record is not None:
                self.free.remove(record)
                record.last_used = time.time()
                self.in_use.append(record)
                return record.connection
            if len(self.free) + len(self.in_use) == self.max_connections:
                if self.free:
                    record = self.free.popleft()
                    record.connection.close()
                else:
                    raise RuntimeError('All database connections are in use')
            connection= create_collection(id)
            record = self.ConnectionRecord(id=id,
                                           creation_time=time.time(),
                                           last_used=time.time(),
                                           connection=connection)
            self.in_use.append(record)
            return record.connection

    def _free_connection(self, connection):
        with self.lock:
            for record in self.in_use:
                if record.connection == connection:
                    break
            else:
                record = None
            if record is not None:
                self.in_use.remove(record)
                record.last_used = time.time()
                self.free.append(record)
    
    def _create_admin_connection(self, unused):
        return psycopg2.connect(dbname=current_app.config['POSTGRES_DATABASE'],
                                port=current_app.config['POSTGRES_PORT'])
        
    def _create_user_connection(self, login):
        with _get_admin_cursor() as cur:
            sql = 'SELECT password FROM cati_portal.identity WHERE login=%s'
            cur.execute(sql, [login])
            encrypted = cur.fetchone()[0].tobytes()
            pg_password = pgp_secret_key().decrypt(pgpy.PGPMessage.from_blob(encrypted)).message[:-22].decode('UTF8')
            return psycopg2.connect(host=current_app.config['POSTGRES_HOST'],
                                    port=current_app.config['POSTGRES_PORT'],
                                    dbname=current_app.config['POSTGRES_DATABASE'],
                                    user=f'cati_portal${login}',
                                    password=pg_password)
    
    def get_admin_connection(self):
        return self._get_connection(None, self._create_admin_connection)
    
    def get_user_connection(self, login):
        return self._get_connection(login, self._create_user_connection)
        
    def free_admin_connection(self, connection):
        self._free_connection(connection)
        
    def free_user_connection(self, login, connection):
        self._free_connection(connection)


class WithDatabaseConnection:
    def __init__(self, login):
        self.login = login
    
    def __enter__(self):
        if self.login is None:
            self.connection = current_app.db_pool.get_admin_connection()
        else:
            self.connection = current_app.db_pool.get_user_connection(self.login)
        return self.connection
    
    def __exit__(self, x, y, z):
        if x is None:
            self.connection.commit()
        else:
            self.connection.rollback()
        if self.login is None:
            current_app.db_pool.free_admin_connection(self.connection)
        else:
            current_app.db_pool.free_user_connection(self.login, self.connection)
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
    return WithDatabaseCursor()

def _get_admin_db():
    return WithDatabaseConnection(None)

def _get_admin_cursor():
    return WithDatabaseCursor(None)
    

def init_app(app):
    app.db_pool = UserConnectionPool()
    #login = pwd.getpwuid(os.getuid()).pw_name
    #app.db_pool = ThreadedConnectionPool(0, 5, app.config['DATABASE'], requirepeer=login)
    

