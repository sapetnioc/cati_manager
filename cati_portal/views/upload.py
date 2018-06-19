from __future__ import absolute_import

from pyramid.view import view_config
from pyramid.httpexceptions import HTTPNotFound

from cati_portal.postgres import user_connect, table_select
from cati_portal.views.admin import check_maintenance

def includeme(config):
    config.add_route('upload', '/upload')
    config.add_route('upload_chunk', '/upload_chunk')

@view_config(route_name='upload', request_method='GET', renderer='templates/upload.jinja2',)
def upload(request):
    check_maintenance(request)
    return {'title': 'Upload'}

@view_config(route_name='upload_chunk', request_method='GET')
def upload_test_chunk(request):
    check_maintenance(request)
    print('Check chunk')
    raise HTTPNotFound()

@view_config(route_name='upload_chunk', request_method='POST', renderer='json',)
def upload_download_chunk(request):
    check_maintenance(request)
    print('Upload POST')
    return {}
