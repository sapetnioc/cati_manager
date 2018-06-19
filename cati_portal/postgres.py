import os
import os.path as osp
from collections import OrderedDict
from datetime import date, datetime
import json
import base64
import threading
import datetime
import importlib
import glob
import hashlib

import psycopg2
import psycopg2.extras
import yaml

from pyramid.exceptions import NotFound




def install_sql_changesets(db, schema, module):
    '''
    Apply all changesets defined in a module in a Postgres schema. The schema
    is created if it does not exist.
    '''
    with db:
        with db.cursor() as cur:
            # Create schema if necessry
            cur.execute("SELECT COUNT(*) FROM information_schema.schemata WHERE schema_name = %s", [schema])
            if not cur.fetchone()[0]:
                cur.execute('CREATE SCHEMA %s;' % schema)
            
            # Create changeset table if necessary
            sql = "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = %s AND table_name = %s;"
            cur.execute(sql, [schema, 'sql_changeset'])
            if not cur.fetchone()[0]:
                cur.execute('CREATE TABLE %s.sql_changeset (module VARCHAR NOT NULL, id VARCHAR NOT NULL, md5 VARCHAR, PRIMARY KEY (module, id));' % schema)
                
            # Check if module is already installed in schema
            cur.execute('SELECT COUNT(*) FROM %s.sql_changeset WHERE module = %%s;' % schema, [module])
            if cur.fetchone()[0]:
                raise ValueError('SQL changesets from module %s are already installed in schema %s' % (module, schema))
            
            # Install sql_changesets
            no_changeset = True
            for id, sql in sql_changesets(module):
                no_changeset = False
                cur.execute(sql)
                sql = "INSERT INTO %s.sql_changeset (module, id, md5) VALUES (%%s, %%s, %%s);" % schema
                cur.execute(sql, [module, id, hashlib.md5(sql.encode('UTF8')).hexdigest()])
            if no_changeset:
                raise ValueError('No sql changeset found in module %s' % module)

class ConnectionPool:
    def __init__(self):
        self.connection_cache = {}
        self.cache_duration = datetime.timedelta(minutes=10)
        self.lock = threading.Lock()
        self.timer = None
    
    def start_timer(self):
        self.timer = threading.Timer(30, self.timer_event)
        self.timer.start()
    
    def connect(self, host, port, database, user, password):
        with self.lock:        
            cache = self.connection_cache.get((host, port, database, user))
            if cache is None:
                connection = psycopg2.connect(host=host,
                                            port=port,
                                            database=database, 
                                            user=user, 
                                            password=password)
            else:
                connection = cache[0]
            self.connection_cache[(host, port, database, user)] = (connection, datetime.datetime.now())
            if self.timer is None:
                self.start_timer()
        return connection

    def timer_event(self):
        with self.lock:
            for k, cache in list(self.connection_cache.items()):
                connection, last_used = cache
                if (datetime.datetime.now() - last_used) > self.cache_duration:
                    connection.close()
                if connection.closed:
                    del self.connection_cache[k]
            if self.connection_cache:
                self.start_timer()
            else:
                self.timer = None
    
    def close_connections(self):
        with self.lock:
            for k, cache in list(self.connection_cache.items()):
                connection, last_used = cache
                connection.close()
            self.connection_cache = {}
        
connection_pool = ConnectionPool()

def manager_connect(request):
    host = request.registry.settings['cati_portal.postgresql_host']
    port = request.registry.settings.get('cati_portal.postgresql_port')
    database = request.registry.settings['cati_portal.database']
    user = request.registry.settings['cati_portal.database_admin']
    password = request.registry.settings['cati_portal.database_admin_challenge']
    return connection_pool.connect(host=host, port=port, database=database, user=user, password=password)


def user_connect(request):
    from cati_portal.authentication import get_user_password
    
    host = request.registry.settings['cati_portal.postgresql_host']
    port = request.registry.settings.get('cati_portal.postgresql_port')
    database = request.registry.settings['cati_portal.database']
    user = request.authenticated_userid
    if not user:
        raise PermissionError('One must be logged in to perform this database action')
    password= get_user_password(request, user)
    if password is None:
        raise PermissionError('Cannot find password for user %s' % user)
    return connection_pool.connect(host=host, port=port, database=database, user='cati_portal$' + user, password=password)


def table_info(db, schema, table):
    '''
    Retrieve information about a Postgres table or view. The result is a
    dictionary with the following items:
    columns: a list of dictionaries describing each column with the
        following items
        id: name of the column
        ordinal_position: index of the column in the list (starting to 1 as
                          in PostgreSQL)
        column_default:
        is_nullable:
        data_type:
        element_type:
    '''
    columns = []
    with db:
        with db.cursor() as cur:
            # First check if schema has column_properties table
            sql = '''SELECT EXISTS (
                SELECT 1
                FROM   information_schema.tables 
                WHERE  table_schema = '{0}'
                AND    table_name = 'column_properties'
            );'''.format(schema)
            cur.execute(sql)
            if cur.fetchone()[0]:
                sql = '''
                    SELECT c.column_name,
                        c.ordinal_position,
                        c.column_default,
                        c.is_nullable,
                        c.data_type,
                        c.character_maximum_length,
                        e.data_type as element_type,
                        f.properties
                    FROM information_schema.columns c LEFT JOIN information_schema.element_types e
                    ON ((c.table_catalog, c.table_schema, c.table_name, 'TABLE', c.dtd_identifier)
                    = (e.object_catalog, e.object_schema, e.object_name, e.object_type, e.collection_type_identifier))
                    LEFT JOIN {0}.column_properties f
                    ON ((c.table_name, c.column_name) = (f.table_name, f.column_name))
                    WHERE c.table_schema = '{0}' AND c.table_name = '{1}'
                    ORDER BY c.ordinal_position;'''.format(schema, table)
            else:
                sql = '''
                    SELECT c.column_name,
                        c.ordinal_position,
                        c.column_default,
                        c.is_nullable,
                        c.data_type,
                        c.character_maximum_length,
                        e.data_type as element_type,
                        NULL
                    FROM information_schema.columns c LEFT JOIN information_schema.element_types e
                    ON ((c.table_catalog, c.table_schema, c.table_name, 'TABLE', c.dtd_identifier)
                    = (e.object_catalog, e.object_schema, e.object_name, e.object_type, e.collection_type_identifier))
                    WHERE c.table_schema = '{0}' AND c.table_name = '{1}'
                    ORDER BY c.ordinal_position;'''.format(schema, table)
            cur.execute(sql)
            names = tuple(i[0] for i in cur.description[:-1])
            for row in cur:
                d = dict((names[i],row[i]) for i in range(1,len(names)))
                column_properties = row[-1]
                if column_properties:
                    d.update(column_properties)
                d['id'] = row[0]
                columns.append(d)
            if not columns:
                sql = '''SELECT count(*) 
                         FROM information_schema.tables AS t 
                         WHERE t.table_schema = '%s' AND t.table_name = '%s';''' % (schema, table)
                cur.execute(sql)
                if cur.fetchone()[0] ==  0:
                    raise NotFound('No database table or view named "%s"' % table)
    return {'columns': columns}

def table_select(db, schema, table, distinct=False, columns=None, where=None,
                 order_by=None, limit=None, offset=None, as_dict=False):
    sql = ['SELECT ']
    if distinct:
        sql.append('DISTINCT ')
    sql += [(','.join(columns) if columns else '*'),
           ' FROM ', ('%s.%s' % (schema, table) if schema else '%s' % table)]
    if where:
        sql += [' WHERE ', where]
    if order_by:
        sql += [' ORDER BY ', ','.join(order_by)]
    if limit:
        sql += [' LIMIT ', limit]
    if offset:
        sql += [' OFFSET ', offset]
    sql = ''.join(sql)
    
    with db:
        if as_dict:
            cur = db.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        else:
            cur = db.cursor()
        with cur:
            cur.execute(sql)
            return cur.fetchall()

def table_insert(db, schema, table, data, columns=None, as_dict=False):
    with db:
        if as_dict:
            cur = db.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        else:
            cur = db.cursor()
        with cur:
            sql_insert = 'INSERT INTO ' + ('%s.%s ' % (schema, table) if schema else '%s ' % table)
            for item in data:
                sql = [sql_insert]
                if columns:
                    cols = columns
                elif isinstance(item, dict):
                    cols = list(item.keys())
                else:
                    cols = None
                if cols:
                    sql += ['( ', ','.join(cols), ' )' ]
                sql.append(' VALUES ( ')
                if cols:
                    sql.append(','.join(['%s'] * len(cols)))
                else:
                    sql.append(','.join(['%s'] * len(item)))
                sql.append(' );')
                sql = ''.join(sql)
                if isinstance(item, dict):
                    row_data = [item[i] for i in cols]
                else:
                    row_data = item
                cur.execute(sql, row_data)
