'''This is the WSGI entry point for cati_portal
'''

from cati_portal import create_app

application = create_app()
