from __future__ import absolute_import

from collections import OrderedDict

from pyramid.view import view_config
from pyramid.exceptions import NotFound

from cati_manager.postgres import rconnect

@view_config(route_name='table_info', renderer='json')
def table_info(request):
    l = request.matchdict['table'].split('.', 1)
    if len(l) < 2:
        schema = 'current_schema'
        table = l[0]
    else:
        schema, table = l
        schema = "'%s'" % schema
    table = "'%s'" % table
    sql = '''
        SELECT c.column_name,
               c.ordinal_position,
               c.column_default,
               c.is_nullable,
               c.data_type,
               c.character_maximum_length,
               e.data_type as element_type 
        FROM information_schema.columns c LEFT JOIN information_schema.element_types e
        ON ((c.table_catalog, c.table_schema, c.table_name, 'TABLE', c.dtd_identifier)
           = (e.object_catalog, e.object_schema, e.object_name, e.object_type, e.collection_type_identifier))
        WHERE c.table_schema = %s AND c.table_name = %s
        ORDER BY c.ordinal_position;''' % (schema, table)
    columns = OrderedDict()
    with rconnect(request) as db:
        with db.cursor() as cur:
            cur.execute(sql)
            names = tuple(i[0] for i in cur.description)
            print(names)
            for row in cur:
                columns[row[0]] = dict((names[i],row[i]) for i in range(1,len(names)))
            if not columns:
                sql = '''SELECT count(*) 
                         FROM information_schema.tables AS t 
                         WHERE t.table_schema = %s AND t.table_name = %s;''' % (schema, table)
                cur.execute(sql)
                if cur.fetchone()[0] ==  0:
                    raise NotFound('No database table or view named "%s"' % request.matchdict['table'])
    return {'columns': columns}
