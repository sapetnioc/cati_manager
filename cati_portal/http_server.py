import os
import subprocess

if __name__ == '__main__':
    env = os.environ.copy()
    env['FLASK_APP'] = 'cati_portal'
    env['FLASK_ENV'] = 'development'
    subprocess.run(['/cati_portal/venv/bin/flask', 'run', '-p', '8080'], env=env)

    #subprocess.run(['/cati_portal/venv/bin/waitress-serve', '--call', 'cati_portal:create_app'])
