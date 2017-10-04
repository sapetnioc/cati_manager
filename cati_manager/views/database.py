from __future__ import absolute_import

from pyramid.view import view_config

from cati_manager.postgres import rconnect, table_info


def includeme(config):
    config.add_route('table_info', '/db/table/{table}/info')
    config.add_route('table_data', '/db/table/{table}/data')
    config.add_route('query_info', '/db/query/{query}/info')
    config.add_route('query_data', '/db/query/{query}/data')
    config.add_route('db_test', '/db/test')


@view_config(route_name='table_info', renderer='json', permission='cati_manager_valid_user')
def table_info_view(request):
    l = request.matchdict['table'].split('.', 1)
    if len(l) < 2:
        schema = 'current_schema'
        table = l[0]
    else:
        schema, table = l
    return table_info(rconnect(request), schema, table)


@view_config(route_name='db_test', renderer='templates/database_form.jinja2')
def db_test(request):
    table_info()
        
