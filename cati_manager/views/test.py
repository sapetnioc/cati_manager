from __future__ import absolute_import

from pyramid.view import view_config

from cati_manager.postgres import manager_connect, table_select
from cati_manager.views.admin import check_maintenance


@view_config(route_name='test', renderer='templates/test.jinja2')
def test(request):
    check_maintenance(request)
    with manager_connect(request) as db:
        schema_templates = table_select(db, 'postgresci', 'project', as_dict=True)
        installed_schemas = table_select(db, 'postgresci', 'installed_component', as_dict=True)
    return {
        'schema_templates': schema_templates,
        'installed_schemas': installed_schemas,
    }

