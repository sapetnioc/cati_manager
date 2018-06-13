from flask import current_app, g

from psycopg2.pool import ThreadedConnectionPool

class WithDatabaseConnection:
    @staticmethod
    def __enter__():
        if 'database_connection' not in g:
            g.database_connection = current_app.db_pool.getconn()
            g.database_connection_use_count = 1
        else:
            g.database_connection_use_count += 1
        return g.database_connection
        
    @staticmethod
    def __exit__(x, y, z):
        g.database_connection_use_count -= 1
        if g.database_connection_use_count == 0:
            if x is None:
                g.database_connection.commit()
            else:
                g.database_connection.rollback()
            current_app.db_pool.putconn(g.database_connection)
            del g.database_connection
            del g.database_connection_use_count
    
class WithDatabaseCursor:
    def __enter__(self):
        connection = WithDatabaseConnection.__enter__()
        self.cursor = connection.cursor()
        return self.cursor.__enter__()
    
    def __exit__(self, x, y, z):
        self.cursor.__exit__(x, y, z)
        WithDatabaseConnection.__exit__(x, y, z)

def get_db():
    '''
    with get_db() as db:
        with db.cursor() as cur:
            cur.execute(...)
    '''
    # WithDatabaseConnection has only static methods, there is no need
    # to instanciate it.
    return WithDatabaseConnection

def get_cursor():
    '''
    with get_cursor() as cur:
        cur.execute(...)
    '''
    return WithDatabaseCursor()


def init_app(app):
    app.db_pool = ThreadedConnectionPool(0, 5, app.config['DATABASE'])
