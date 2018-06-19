from __future__ import absolute_import

from pyramid.view import view_config
from pyramid.security import Authenticated

from cati_portal.postgres import (user_connect,
                                   table_select)
from cati_portal.views.admin import check_maintenance

def includeme(config):
    config.add_route('project', '/project')

@view_config(route_name='project', request_method='GET', renderer='templates/layout.jinja2',
             permission=Authenticated)
def projects(request):
    check_maintenance(request)
    with user_connect(request) as db:
        with db.cursor() as cur:
            result = table_select(db, 'cati_portal', 'my_projects', as_dict=True)
    return {'title': 'Projects',
            'content': result}

