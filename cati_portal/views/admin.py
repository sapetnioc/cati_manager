from __future__ import absolute_import

import os
import os.path as osp
import json
import base64

from pyramid.view import view_config
from pyramid.httpexceptions import HTTPFound
import psycopg2.extras

from cati_portal.postgres import manager_connect, connection_pool


class MaintenanceError(Exception):
    pass


def includeme(config):
    config.add_route('admin', '/admin')
    config.add_route('maintenance', '/maintenance')


def check_maintenance(request):
    maintenance_path = osp.expanduser(request.registry.settings['cati_portal.maintenance_path'])
    if osp.exists(maintenance_path):
        raise MaintenanceError('Service is down for maintenance.')


@view_config(route_name='admin', request_method='GET', renderer='templates/admin.jinja2', permission='cati_portal_server_admin')
def admin(request):
    result = { 'maintenance': None }
    maintenance_path = osp.expanduser(request.registry.settings['cati_portal.maintenance_path'])
    if osp.exists(maintenance_path):
        result['maintenance'] = json.load(open(maintenance_path))
    else:
        database = request.registry.settings['cati_portal.database']
        admin = request.registry.settings['cati_portal.database_admin']
        with manager_connect(request) as db:
            with db.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                sql = 'SELECT pid, usename AS login, backend_start, xact_start, query_start, state_change, state, query FROM pg_stat_activity WHERE datname = %s AND usename != %s;'
                cur.execute(sql, [database, admin])
                result['database_connections'] = cur.fetchall()
        
    return result

@view_config(route_name='maintenance', request_method='POST', permission='cati_portal_server_admin')
def start_maintenance(request):
    maintenance_path = osp.expanduser(request.registry.settings['cati_portal.maintenance_path'])
    if osp.exists(maintenance_path):
        os.remove(maintenance_path)
    else:
        maintenance = {
            'message': request.params['message'],
            'maintenance_end': request.params['maintenance_end'],
            'admins': {},
        }
        with manager_connect(request) as db:
            with db.cursor() as cur:
                sql = "SELECT i.login, i.password FROM cati_portal.identity i LEFT JOIN cati_portal.granting g ON i.login = g.login WHERE g.project = 'cati_portal' AND g.credential = 'server_admin';"
                cur.execute(sql)
                for i in cur:
                    maintenance['admins'][i[0]] = base64.b64encode(i[1]).decode('utf-8')
        connection_pool.close_connections()
        json.dump(maintenance, open(maintenance_path, 'w'))
    raise HTTPFound(request.route_url('admin'))
