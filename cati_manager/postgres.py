from collections import OrderedDict

import psycopg2

from pyramid.exceptions import NotFound


connections = {}
def connect(database_url, database_user, database_password, target_user):
    global connections
    
    connection = connections.get((database_url, target_user))
    if connection is None:
        connection = psycopg2.connect(database_url, user=database_user, password=database_password)
        if target_user is not None:
            connection.cursor().execute('SET ROLE ?;', (target_user,))
            connection.commit()
            connections[(database_url, target_user)] = connection
    return connection


def rconnect(request, user=None):
    database_url = request.registry.settings['cati_manager.database']
    database_user = request.registry.settings['cati_manager.database_user']
    database_password = request.registry.settings['cati_manager.database_password']
    return connect(database_url, database_user, database_password, user)


def authentication_callback(login, request):
    '''
    ldap_authentication_callback can be used as callback for
    AuthTktAuthenticationPolicy. It checks user password and 
    returns either None if the user is not authenticated or a
    list composed of the user login and the groups it
    belongs to (each group name is added a prefix 'group:').
    '''
    with rconnect(request) as db:
        with db.cursor() as cur:
            cur.execute('SELECT DISTINCT credential.project, credential.id FROM identity, granting, project, credential WHERE identity.login=%s AND granting.login = identity.login AND credential.id = granting.credential', (login,))
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
    columns = OrderedDict()
    with db:
        with db.cursor() as cur:
            cur.execute(sql)
            names = tuple(i[0] for i in cur.description[:-1])
            for row in cur:
                d = dict((names[i],row[i]) for i in range(1,len(names)))
                column_properties = row[-1]
                if column_properties:
                    d.update(column_properties)
                columns[row[0]] = d
            if not columns:
                sql = '''SELECT count(*) 
                         FROM information_schema.tables AS t 
                         WHERE t.table_schema = %s AND t.table_name = '%s';''' % (schema, table)
                cur.execute(sql)
                if cur.fetchone()[0] ==  0:
                    raise NotFound('No database table or view named "%s"' % table)
    return {'columns': columns}

def pg2html_text(column_name, label, column_info):
    return '<div class="form-group" name="{0}"><label class="from-control-label" for="{0}">{1}:&nbsp;</label><input name="{0}" type="text" class="form-control" placeholder="{1}"></div>'.format(column_name, label)

select_pg2html_from_postgres_type = {
    'text': pg2html_text,
}

def table_to_form_widgets(table_info):
    widgets = []
    for column_name, column_info in table_info['columns'].items():
        if column_info.get('visible', True):
            pg2html = select_pg2html_from_postgres_type.get(column_info['data_type'])
            if pg2html:
                label = column_info.get('label', column_name)
                widgets.append(pg2html(column_name, label, column_info))
                if column_info.get('double_check', False):
                    widgets.append(pg2html('double_check_' + column_name, 'check ' + label, column_info))
            else:
                widgets.append('<font color="red"><b>{0}: cannot create widget for data type "{1}"</b></font>'.format(column_name, column_info['data_type']))
    return widgets