import html
import traceback

import psycopg2

from pyramid.view import view_config


@view_config(context=Exception, renderer='templates/exceptions.jinja2')
def uncaught_exception(exc, request):
    return {'error_type': 'Internal error',
            'error_messages': ['<strong>%s</strong>: %s' % (exc.__class__.__name__, html.escape(str(exc)).replace('\n','<br>'))],
            'technical_messages': ['\n'.join(traceback.format_exception(exc.__class__,exc,exc.__traceback__))]}

@view_config(context=psycopg2.Error, renderer='templates/exceptions.jinja2')
def database_exception(exc, request):
    result = uncaught_exception(exc, request)
    result['error_type'] = 'Database error'
    if exc.cursor and exc.cursor.query:
        result['technical_messages'].insert(0, '<strong>SQL Query:</strong><br>%s' % exc.cursor.query.decode())
    return result