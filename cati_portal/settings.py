import os
import os.path as osp

from flask import Blueprint, render_template, url_for, redirect, abort
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, validators

from .home import RegistrationForm
from cati_portal.authentication import check_password

bp = Blueprint('settings', __name__, url_prefix='/settings')

@bp.route('/install', methods=('GET', 'POST'))
def install():
    hash_file = osp.join(os.environ.get('CATI_PORTAL_DIR', '/cati_portal'), 'tmp', 'installation.hash')
    if osp.exists(hash_file):
        form = RegistrationForm()
        if form.validate_on_submit():
            hash = open(hash_file, 'rb').read()
            if check_password(form.install_code.data, hash):
                return redirect(url_for('settings.settings'))
            abort(403)
        return render_template('register.html', form=form)
    abort(404)

class SettingsForm(FlaskForm):
    login     = StringField('smtp_server')
    submit = SubmitField('Save settings')

@bp.route('')
def settings():
    form = SettingsForm()
    if form.validate_on_submit():
        return redirect(url_for('home.main'))
    return render_template('register.html', title='Server settings', form=form)
