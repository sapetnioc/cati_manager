import subprocess
import json


if __name__ == '__main__':
    # Extract port and worker count from configuration
    config = json.load(open('/cati_portal/flask_instance/config.json'))
    port = config.get('HTTP_PORT', '8080')
    workers = config.get('WORKERS_COUNT', 4)

    # Start HTTP server with Gunicorn
    subprocess.run(['/cati_portal/venv/bin/gunicorn',
                    '--preload',
                    '-w', str(workers),
                    '-b', '0.0.0.0:%s' % port,
                    '--access-logfile', '/cati_portal/log/cati_portal.log',
                    '--error-logfile', '/cati_portal/log/cati_portal.log',
                    'cati_portal.wsgi'],
                   stdout=open('/cati_portal/log/cati_portal.log', 'a'),
                   stderr=subprocess.STDOUT)
