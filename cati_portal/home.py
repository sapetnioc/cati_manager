import os
import os.path as osp

from flask import Blueprint, render_template, url_for, redirect, flash  
from flask_wtf import FlaskForm
from flask_login import current_user, login_user, login_required, logout_user
from wtforms import StringField, PasswordField, HiddenField, SubmitField, validators
from wtforms.widgets import HiddenInput

from cati_portal.authentication import User
from cati_portal import db
from cati_portal.form import RedirectForm

bp = Blueprint('home', __name__, url_prefix='/')

@bp.route('')
def index():
    hash_file = osp.join(os.environ.get('CATI_PORTAL_DIR', '/cati_portal'), 'tmp', 'installation.hash')
    if osp.exists(hash_file):
        return redirect(url_for('authentication.install'))
    return render_template('home.html')

