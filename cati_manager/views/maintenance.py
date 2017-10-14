import os.path as osp

class MaintenanceError(Exception):
    pass

def check_maintenance(request):
    maintenance_path = osp.expanduser(request.registry.settings['cati_manager.maintenance_path'])
    if osp.exists(maintenance_path):
        raise MaintenanceError('Service is down for maintenance.')
