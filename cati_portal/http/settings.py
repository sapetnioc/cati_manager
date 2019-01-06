import json
import os
import os.path as osp

from flask import (Blueprint, render_template, url_for, redirect, current_app)
from flask_wtf import FlaskForm
from flask_login import login_required
from wtforms import StringField, SubmitField

from cati_portal.db import get_db

bp = Blueprint('settings', __name__, url_prefix='/settings')


class SettingsForm(FlaskForm):
    smtp_server = StringField('smtp_server')
    submit = SubmitField('Save settings')

@bp.route('', methods=('GET', 'POST'))
@login_required
def settings():
    with get_db() as db:
        form = SettingsForm(smtp_server = current_app.config.get('SMTP_SERVER', ''))
        if form.validate_on_submit():
            current_app.config['SMTP_SERVER'] = form.smtp_server.data
            config_file = osp.join(current_app.instance_path, 'config.json')
            if osp.exists(config_file):
                config = json.load(open(config_file))
                config['SMTP_SERVER'] = current_app.config['SMTP_SERVER']
                json.dump(config, open(config_file, 'w'), indent=4)
            return redirect(url_for('home.index'))
        return render_template('form_page.html', title='Server settings', form=form)
