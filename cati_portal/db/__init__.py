import os
import pwd
import threading

from flask import current_app, g
from flask_login import current_user
import pgpy
import psycopg2


class UserConnectionPool:
    def get_admin_connection(self):
        cnx = psycopg2.connect(dbname=current_app.config['POSTGRES_DATABASE'],
                               port=current_app.config['POSTGRES_PORT'])
        return cnx
    
    def free_admin_connection(self, connection):
        connection.close()
    
    def get_user_connection(self, login):
        from cati_portal.authentication import pgp_secret_key
        with _get_admin_cursor() as cur:
            sql = 'SELECT password FROM cati_portal.identity WHERE login=%s'
            cur.execute(sql, [login])
            encrypted = cur.fetchone()[0].tobytes()
            pg_password = pgp_secret_key().decrypt(pgpy.PGPMessage.from_blob(encrypted)).message[:-22].decode('UTF8')
        cnx = psycopg2.connect(host=current_app.config['POSTGRES_HOST'],
                               port=current_app.config['POSTGRES_PORT'],
                               dbname=current_app.config['POSTGRES_DATABASE'],
                               user=f'cati_portal${login}',
                               password=pg_password)
                         
        return cnx
    
    def free_user_connection(self, login, connection):
        connection.close()
        
        
        
    #def __enter__():
        #user = current_user
        #if user.is_authenticated and user.is_active:
            #user_id = user.get_id()
            #with self.lock:
                #cnx = self.free_connections.pop(user_id, None)
                #if cnx:
                    #self.connections_in_use[user_id] = 
            #if 'database_connection' not in g:
                #g.database_connection = current_app.db_pool.getconn()
                #g.database_connection_use_count = 1
            #else:
                #g.database_connection_use_count += 1
            #return g.database_connection
        #else:
            #raise RuntimeError('insuficient rights to connect to the database')


        #g.database_connection_use_count -= 1
        #if g.database_connection_use_count == 0:
            #if x is None:
                #g.database_connection.commit()
            #else:
                #g.database_connection.rollback()
            #current_app.db_pool.putconn(g.database_connection)
            #del g.database_connection
            #del g.database_connection_use_count



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
    

