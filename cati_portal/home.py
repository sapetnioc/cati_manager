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
def main():
    hash_file = osp.join(os.environ.get('CATI_PORTAL_DIR', '/cati_portal'), 'tmp', 'installation.hash')
    if osp.exists(hash_file):
        return redirect(url_for('settings.install'))
    return render_template('home.html')

class LoginForm(RedirectForm):
    login     = StringField('login', [validators.DataRequired()])
    password = PasswordField('Password', validators=[validators.DataRequired()])
    submit = SubmitField('Sign in')

@bp.route('/login', methods=('GET', 'POST'))
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home.main'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User(form.login.data)
        if user.login is None or not user.check_password(form.password.data):
            flash('Invalid username or password', 'warning')
            return redirect(url_for('home.login'))
        login_user(user)
        return form.redirect('home.main')
    return render_template('form_page.html', form=form, title='Sign in')

@bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home.main'))


class RegistrationForm(FlaskForm):
    login     = StringField('login', [validators.DataRequired(), validators.Length(min=4, max=25)], render_kw=dict(size=32))
    email        = StringField('Email Address', [validators.DataRequired(), validators.Email()])
    password = PasswordField('Password', validators=[validators.DataRequired(), validators.EqualTo('confirm_password', message='Passwords does not match')])
    confirm_password = PasswordField('Confirm password', validators=[validators.DataRequired()])
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
    return render_template('form_page.html', form=form)
