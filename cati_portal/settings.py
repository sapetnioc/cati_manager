import os
import os.path as osp

from flask import Blueprint, render_template, url_for, redirect, abort, flash
from flask_wtf import FlaskForm
from flask_login import login_required
from wtforms import StringField, PasswordField, SubmitField, validators

from .home import RegistrationForm
from cati_portal.authentication import check_password, User
from cati_portal.db import get_db

bp = Blueprint('settings', __name__, url_prefix='/settings')

@bp.route('/install', methods=('GET', 'POST'))
def install():
    hash_file = osp.join(os.environ.get('CATI_PORTAL_DIR', '/cati_portal'), 'tmp', 'installation.hash')
    if osp.exists(hash_file):
        form = RegistrationForm()
        if form.validate_on_submit():
            hash = open(hash_file, 'rb').read()
            if check_password(form.install_code.data, hash):
                user = User.new(login = form.login.data,
                                email = form.email.data,
                                password = form.password.data,
                                first_name = form.first_name.data,
                                last_name = form.last_name.data,
                                institution = form.institution.data)
                user.validate_email()
                flash(f'Administrator {form.login.data} succesfully registered and validated', 'success')
                return redirect(url_for('settings.settings'))
            flash('Invalid installation code', 'danger')
        return render_template('form_page.html', title='Administrator registration', form=form)
    abort(404)

class SettingsForm(FlaskForm):
    login     = StringField('smtp_server')
    submit = SubmitField('Save settings')

@bp.route('')
@login_required
def settings():
    with get_db() as db:
        form = SettingsForm()
        if form.validate_on_submit():
            return redirect(url_for('home.main'))
        return render_template('form_page.html', title='Server settings', form=form)
