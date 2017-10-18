from __future__ import absolute_import

from pyramid.view import view_config

from cati_manager.postgres import (user_connect, 
                                   table_info,
                                   table_select,
                                   table_insert)
from cati_manager.views.admin import check_maintenance



def includeme(config):
    config.add_route('table_info', '/db/table/{table}/info')
    config.add_route('table_data', '/db/table/{table}/data')


@view_config(route_name='table_info', request_method='GET', renderer='json', permission='cati_manager_valid_user')
def table_info_view(request):
    check_maintenance(request)
    l = request.matchdict['table'].split('.', 1)
    if len(l) < 2:
        schema = 'current_schema'
        table = l[0]
    else:
        schema, table = l
    return table_info(user_connect(request), schema, table)

@view_config(route_name='table_data', request_method='GET', renderer='json2', permission='cati_manager_valid_user')
def table_data_view(request):
    check_maintenance(request)
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
    return table_select(user_connect(request), **kwargs)


@view_config(route_name='table_data', request_method='POST', renderer='json2', permission='cati_manager_valid_user')
def table_data_view(request):
    check_maintenance(request)
    l = request.matchdict['table'].split('.', 1)
    if len(l) < 2:
        schema = 'current_schema'
        table = l[0]
    else:
        schema, table = l
    kwargs = dict(schema=schema, table=table)
    as_list = request.params.get('as_list')
    if as_list is not None:
        kwargs['as_list'] = True
    columns = request.params.get('columns')
    if columns:
        kwargs['columns'] = columns.split(',')
    return table_insert(user_connect(request), **kwargs)

        
