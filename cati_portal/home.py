import os
import os.path as osp

from flask import Blueprint, render_template, url_for, redirect
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, validators
from wtforms.widgets import HiddenInput

from . import db

bp = Blueprint('home', __name__, url_prefix='/')

@bp.route('')
def main():
    hash_file = osp.join(os.environ.get('CATI_PORTAL_DIR', '/cati_portal'), 'tmp', 'installation.hash')
    if osp.exists(hash_file):
        form = RegistrationForm()
        if form.validate_on_submit():
            return redirect(url_for('home.main'))
        return render_template('register.html', title='Admin user registration', form=form)
        
    return render_template('home.html')
    #with db.get_cursor() as cur:
        #cur.execute('SELECT * FROM cati_portal.identity;')
        #return str(cur.fetchall())

@bp.route('/login')
def login():
    return render_template('home.html', title='Login')


class RegistrationForm(FlaskForm):
    login     = StringField('login', [validators.DataRequired(), validators.Length(min=4, max=25)], render_kw=dict(size=32))
    email        = StringField('Email Address', [validators.DataRequired(), validators.Length(min=6, max=35)])
    password = PasswordField('Password', validators=[validators.DataRequired()])
    password2 = PasswordField('Confirm password', validators=[validators.DataRequired()])
    first_name = StringField('First name', [validators.Length(max=40)])
    last_name = StringField('Last name', [validators.Length(max=40)])
    institution = StringField('Institution', [validators.Length(max=40)])
    install_code = StringField('Installation code', [validators.Length(max=16)])
    submit = SubmitField('Register')

@bp.route('/register', methods=('GET', 'POST'))
def register():
    form = RegistrationForm()
    form.install_code.widget = HiddenInput()
    form.install_code.flags.hidden = True
    if form.validate_on_submit():
        return redirect(url_for('home.main'))
    return render_template('register.html', form=form)
