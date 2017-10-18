from __future__ import absolute_import

import os
import os.path as osp
import json
import base64

from pyramid.view import view_config
import psycopg2.extras

from cati_manager.postgres import manager_connect, table_select


class MaintenanceError(Exception):
    pass


def includeme(config):
    config.add_route('maintenance', '/maintenance')


def check_maintenance(request):
    maintenance_path = osp.expanduser(request.registry.settings['cati_manager.maintenance_path'])
    if osp.exists(maintenance_path):
        raise MaintenanceError('Service is down for maintenance.')


@view_config(route_name='maintenance', request_method='GET', renderer='templates/maintenance.jinja2', permission='cati_manager_server_admin')
def maintenance_status(request):
    result = { 'maintenance': None }
    maintenance_path = osp.expanduser(request.registry.settings['cati_manager.maintenance_path'])
    if osp.exists(maintenance_path):
        result['maintenance'] = json.load(open(maintenance_path))
    else:
        database = request.registry.settings['cati_manager.database']
        admin = request.registry.settings['cati_manager.database_admin']
        with manager_connect(request) as db:
            with db.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                sql = 'SELECT pid, usename AS login, backend_start, xact_start, query_start, state_change, state, query FROM pg_stat_activity WHERE datname = %s AND usename != %s;'
                cur.execute(sql, [database, admin])
                result['database_connections'] = cur.fetchall()
    return result

@view_config(route_name='maintenance', request_method='POST', renderer='templates/maintenance.jinja2', permission='cati_manager_server_admin')
def start_maintenance(request):
    maintenance_path = osp.expanduser(request.registry.settings['cati_manager.maintenance_path'])
    if osp.exists(maintenance_path):
        os.remove(maintenance_path)
        maintenance = None
    else:
        maintenance = {
            'message': request.params['message'],
            'maintenance_end': request.params['maintenance_end'],
        }
        with manager_connect(request) as db:
            with db.cursor() as cur:
                sql = "SELECT i.login, i.password FROM cati_manager.identity i LEFT JOIN cati_manager.granting g ON i.login = g.login WHERE g.project = 'cati_manager' AND g.credential = 'server_admin';"
                cur.execute(sql)
                maintenance['admins'] = []
                for i in cur:
                    maintenance['admins'].append([i[0], base64.b64encode(i[1]).decode('utf-8')])
        json.dump(maintenance, open(maintenance_path, 'w'))
    return {'maintenance': maintenance}
