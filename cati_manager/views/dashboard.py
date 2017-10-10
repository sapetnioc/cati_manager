from __future__ import absolute_import

from pyramid.view import view_config

from cati_manager.postgres import user_connect, table_select

def includeme(config):
    config.add_route('dashboard', '/dashboard')

@view_config(route_name='dashboard', renderer='templates/home.jinja2',
             permission='cati_manager_valid_user')
def dashboard(request):
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
                #sql = ('SELECT login, first_name, last_name '
                       #'FROM cati_manager.identity_not_validated;')
                #cur.execute(sql)
                #if cur.rowcount:
                    #users = []
                    #dashboards.append({
                        #'item_type': 'user_not_validated',
                        #'items': users})
                    #for row in cur:
                        #users.append(dict(login=row[0], first_name=row[1], last_name=row[2]))
                #sql = ('SELECT login, first_name, last_name '
                       #'FROM cati_manager.identity_email_not_verified;')
                #cur.execute(sql)
                #if cur.rowcount:
                    #users = []
                    #dashboards.append({
                        #'item_type': 'user_email_not_verified',
                        #'items': users})
                    #for row in cur:
                        #users.append(dict(login=row[0], first_name=row[1], last_name=row[2]))
    return {'title': 'Dashboard',
            'dashboards': dashboards}
