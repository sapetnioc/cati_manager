from __future__ import absolute_import

from pyramid.view import view_config

from cati_manager.postgres import rconnect

def includeme(config):
    config.add_route('dashboard', '/dashboard')

@view_config(route_name='dashboard', renderer='templates/home.jinja2',
             permission='cati_manager_valid_user')
def dashboard(request):
    dashboards = []
    if request.has_permission('cati_manager_user_moderator'):
        with rconnect(request) as db:
            with db.cursor() as cur:
                sql = '''SELECT i.login, i.first_name, i.last_name
FROM cati_manager.identity i
WHERE i.login != 'cati_manager' AND
      i.login NOT IN
          (SELECT login 
           FROM cati_manager.granting g 
           WHERE g.project = 'cati_manager' AND 
                 g.credential = 'valid_user');'''
                cur.execute(sql)
                if cur.rowcount:
                    users = []
                    dashboards.append({
                        'title': 'Users to validate',
                        'title_glyphicon': 'user',
                        'lines': users})
                    for row in cur:
                        users.append(row[0])
    return {'title': 'Dashboard',
            'dashboards': dashboards}
