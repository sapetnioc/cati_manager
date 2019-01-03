import os
import subprocess
import json

if __name__ == '__main__':
    env = os.environ.copy()
    env['FLASK_APP'] = 'cati_portal'
    env['FLASK_ENV'] = 'development'
    config = {}
    config = json.load(open('/cati_portal/flask_instance/config.json'))
    subprocess.run(['/cati_portal/venv/bin/flask', 'run', '-p', config.get('HTTP_PORT', '8080')], env=env)

    #subprocess.run(['/cati_portal/venv/bin/waitress-serve', '--call', 'cati_portal:create_app'])
