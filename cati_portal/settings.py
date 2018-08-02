import os
import os.path as osp

from flask import Blueprint, render_template, url_for, redirect
from flask_wtf import FlaskForm
from flask_login import login_required
from wtforms import StringField, SubmitField

from cati_portal.db import get_db

bp = Blueprint('settings', __name__, url_prefix='/settings')


class SettingsForm(FlaskForm):
    smtp_server = StringField('smtp_server')
    submit = SubmitField('Save settings')

@bp.route('')
@login_required
def settings():
    with get_db() as db:
        form = SettingsForm()
        if form.validate_on_submit():
            return redirect(url_for('home.index'))
        return render_template('form_page.html', title='Server settings', form=form)
