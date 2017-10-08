from __future__ import absolute_import

from pyramid.view import view_config

from cati_manager.postgres import manager_connect, table_info


@view_config(route_name='test', renderer='templates/database_form.jinja2')
def test(request):
    ti = table_info(manager_connect(request), 'cati_manager', 'identity')
    widgets = table_to_form_widgets(ti)
    return {
        'form_widgets': widgets,
        'form_buttons': ['<input name="register" type="submit" value="Register">'],
    }

