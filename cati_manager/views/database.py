from __future__ import absolute_import

from pyramid.view import view_config

from cati_manager.postgres import (rconnect, 
                                   table_info,
                                   table_data)



def includeme(config):
    config.add_route('table_info', '/db/table/{table}/info')
    config.add_route('table_data', '/db/table/{table}/data')
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

@view_config(route_name='table_data', renderer='json2', permission='cati_manager_valid_user')
def table_data_view(request):
    l = request.matchdict['table'].split('.', 1)
    if len(l) < 2:
        schema = 'current_schema'
        table = l[0]
    else:
        schema, table = l
    kwargs = dict(schema=schema, table=table)
    limit = request.params.get('limit')
    if limit:
        kwargs['limit'] = limit
    offset = request.params.get('offset')
    if offset:
        kwargs['offset'] = offset
    as_list = request.params.get('as_list')
    if as_list is not None:
        kwargs['as_list'] = True
    columns = request.params.get('columns')
    if columns:
        kwargs['columns'] = columns.split(',')
    order_by = request.params.get('order_by')
    if order_by:
        kwargs['order_by'] = order_by.split(',')
    where = request.params.get('where')
    if where:
        kwargs['where'] = where
    return table_data(rconnect(request), **kwargs)


@view_config(route_name='db_test', renderer='templates/database_form.jinja2')
def db_test(request):
    table_info()
        
