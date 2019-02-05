import json
import os
import os.path as osp

from flask import (Blueprint, render_template, url_for, redirect, current_app)
from flask_wtf import FlaskForm
from flask_login import login_required
from wtforms import StringField, PasswordField, SubmitField, validators

bp = Blueprint('settings', __name__, url_prefix='/settings')


class SettingsForm(FlaskForm):
    '''
    This form defines the fields that compose the cati_portal server
    configuration. These fields can be edited in the /settings page and
    are stored in the flask server configuration. This configuration is
    stored on disk in a JSON file that is read at server startup.
    '''
    smtp_server = StringField('SMTP server')
    smtp_login = StringField('SMTP login')
    smtp_password = PasswordField('SMTP password', validators=[validators.EqualTo('confirm_smtp_password', message="Passwords and confirmation don't match")])
    confirm_smtp_password = PasswordField('Confirm SMTP password')

    submit = SubmitField('Save settings')

    def __init__(self, *args, **kwargs):
        super(SettingsForm, self).__init__(*args, **kwargs)
        self.confirm_smtp_password.flags.not_in_config = True


@bp.route('', methods=('GET', 'POST'))
@login_required
def settings():
    form = SettingsForm()
    config = None
    if form.validate_on_submit():
        config_file = osp.join(current_app.instance_path, 'config.json')
        if osp.exists(config_file):
            config = json.load(open(config_file))
        for field in form:
            if field.type == 'SubmitField' or field.short_name == 'csrf_token':
                continue
            if field.type == 'PasswordField' and not field.data:
                continue
            current_app.config[field.short_name.upper()] = field.data
            if config is not None and not field.flags.not_in_config:
                config[field.short_name.upper()] = field.data
        if config is not None:
            json.dump(config, open(config_file, 'w'), indent=4)
        # return redirect(url_for('home.index'))
    else:
        for field in form:
            value = current_app.config.get(field.short_name.upper())
            if value is not None:
                field.data = value
    return render_template('form_page.html', title='Server settings', form=form)
