from __future__ import absolute_import

from pyramid.view import view_config

from cati_manager.postgres import user_connect, table_select
from cati_manager.views.admin import check_maintenance

def includeme(config):
    config.add_route('dashboard', '/dashboard')

@view_config(route_name='dashboard', renderer='templates/home.jinja2',
             permission='cati_manager_valid_user')
def dashboard(request):
    check_maintenance(request)
    dashboards = []
    with user_connect(request) as db:
        with db.cursor() as cur:
            if request.has_permission('cati_manager_user_moderator'):
                items = table_select(db, 'cati_manager', 'identity_email_not_verified', as_dict=True)
                if items:
                    dashboards.append({
                        'item_type': 'user_email_not_verified',
                        'items': items})
                items = table_select(db, 'cati_manager', 'identity_not_validated', as_dict=True)
                if items:
                    dashboards.append({
                        'item_type': 'user_not_validated',
                        'items': items})
    return {'title': 'Dashboard',
            'dashboards': dashboards}
