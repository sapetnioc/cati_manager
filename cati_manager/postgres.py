from collections import OrderedDict
from datetime import date, datetime
import json
import base64

import psycopg2
import psycopg2.extras

from pyramid.exceptions import NotFound


connections = {}
def connect(host, port, database, user, password):
    global connections
        
    connection = connections.get((host, port, database, user))
    if connection is None:
        connection = psycopg2.connect(host=host,
                                      port=port,
                                      database=database, 
                                      user=user, 
                                      password=password)
        connections[(host, port, database, user)] = connection
    return connection


def manager_connect(request):
    host = request.registry.settings['cati_manager.postgresql_host']
    port = request.registry.settings.get('cati_manager.postgresql_port')
    database = request.registry.settings['cati_manager.database']
    user = request.registry.settings['cati_manager.database_admin']
    password = request.registry.settings['cati_manager.database_admin_challenge']
    return connect(host=host, port=port, database=database, user=user, password=password)


def user_connect(request):
    host = request.registry.settings['cati_manager.postgresql_host']
    port = request.registry.settings.get('cati_manager.postgresql_port')
    database = request.registry.settings['cati_manager.database']
    user = request.authenticated_userid
    if not user:
        raise PermissionError('One must be logged in to perform this database action')
    with manager_connect(request) as db:
        with db.cursor() as cur:
            cur.execute('SELECT password FROM cati_manager.identity WHERE login=%s', [user])
            if cur.rowcount:
                password = base64.b64encode(cur.fetchone()[0].tobytes()).decode()
                return connect(host=host, port=port, database=database, user='cati_manager$' + user, password=password)
            else:
                raise PermissionError('Unknown user %s' % user)


def authentication_callback(login, request):
    '''
    ldap_authentication_callback can be used as callback for
    AuthTktAuthenticationPolicy. It checks user password and 
    returns either None if the user is not authenticated or a
    list composed of the user login and the groups it
    belongs to (each group name is added a prefix 'group:').
    '''
    with manager_connect(request) as db:
        with db.cursor() as cur:
            cur.execute('SELECT DISTINCT credential.project, credential.id FROM identity, granting, project, credential WHERE identity.login=%s AND granting.login = identity.login AND credential.id = granting.credential', [login])
            principals = ['%s_%s' % i for i in cur]
    return [ login ] + principals


def table_info(db, schema, table):
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
    columns = []
    with db:
        with db.cursor() as cur:
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
                         WHERE t.table_schema = %s AND t.table_name = '%s';''' % (schema, table)
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
