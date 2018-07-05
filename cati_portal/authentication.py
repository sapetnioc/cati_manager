import datetime 
import os
import os.path as osp

from flask import Blueprint, render_template, url_for, redirect, flash, abort
from flask_wtf import FlaskForm
from flask_login import current_user, login_user, login_required, logout_user
import pgpy
from wtforms import StringField, PasswordField, HiddenField, SubmitField, validators
from wtforms.widgets import HiddenInput

from cati_portal.db import _get_admin_cursor
from cati_portal.encryption import check_password
from cati_portal.form import RedirectForm

bp = Blueprint('authentication', __name__, url_prefix='/authentication')

class LoginForm(RedirectForm):
    login     = StringField('login', [validators.DataRequired()])
    password = PasswordField('Password', validators=[validators.DataRequired()])
    submit = SubmitField('Sign in')

class User:
    def __init__(self, login, email, first_name, last_name, institution,
                 is_authenticated, is_active, is_anonymous):
        self.login = login
        self.email = email
        self.first_name = first_name
        self.last_name = last_name
        self.institution = institution
        self.is_authenticated = is_authenticated
        self.is_active = is_active
        self.is_anonymous = is_anonymous
    
    
    @staticmethod
    def get(login):
        with _get_admin_cursor() as cur:
            sql = 'SELECT email, first_name, last_name, institution, email_verification_time, activation_time, deactivation_time FROM cati_portal.identity WHERE login = %s'
            cur.execute(sql, [login])
            if cur.rowcount:
                email, first_name, last_name, institution, email_verification_time, activation_time, deactivation_time = cur.fetchone()
                is_authenticated = True
                is_active = (activation_time is not None and email_verification_time is not None and deactivation_time is None)
                is_anonymous = False
                return User(login=login,
                            email=email,
                            first_name=first_name,
                            last_name=last_name,
                            institution=institution,
                            is_authenticated=is_authenticated,
                            is_active=is_active,
                            is_anonymous=is_anonymous)
        return None
    
    @staticmethod
    def create(login, password, email, first_name=None, last_name=None, institution=None):
        '''
        Create a new user in the database
        '''
        with _get_admin_cursor() as cur:
            sql = 'INSERT INTO cati_portal.identity(login, password, email, first_name, last_name, institution) VALUES (%s, %s, %s, %s, %s, %s)'
            cur.execute(sql, [login, password, email, first_name, last_name, institution])
        return User.get(login)
    

    def get_id(self):
        return self.login
    
    def check_password(self, password):
        '''
        Check the password of a user
        '''
        if self.login:
            with _get_admin_cursor() as cur:
                sql = 'SELECT password FROM cati_portal.identity WHERE login = %s'
                cur.execute(sql, [self.login])
                if cur.rowcount == 1:
                    hash = cur.fetchone()[0].tobytes()
                    return check_password(password, hash)
        return False
    
    def has_credential(self, required):
        '''
        Verify that the user has a credential
        '''
        if self.is_active:
            l = required.split('.', 1)
            if len(l) != 2:
                raise ValueError(f'Invalid credential string "{required}". It must have the form "<project>.<credential>".')
            project, credential = l
            with _get_admin_cursor() as cur:
                sql = 'SELECT COUNT(*) FROM cati_portal.granting WHERE project = %s AND credential = %s AND login = %s'
                cur.execute(sql, [project, credential, self.login])
                return (cur.fetchone()[0] == 1)
        return False

@bp.route('/install', methods=('GET', 'POST'))
def install():
    hash_file = osp.join(os.environ.get('CATI_PORTAL_DIR', '/cati_portal'), 'tmp', 'installation.hash')
    if osp.exists(hash_file):
        form = RegistrationForm()
        if form.validate_on_submit():
            hash = open(hash_file, 'rb').read()
            if check_password(form.install_code.data, hash):
                user = User.create(login = form.login.data,
                                   email = form.email.data,
                                   password = form.password.data,
                                   first_name = form.first_name.data,
                                   last_name = form.last_name.data,
                                   institution = form.institution.data)
                with _get_admin_cursor() as cur:
                    time = datetime.datetime.now()
                    sql = 'UPDATE cati_portal.identity SET activation_time = %s, email_verification_time = %s WHERE login = %s;'
                    cur.execute(sql, [time, time, user.login])
                    sql = 'INSERT INTO cati_portal.granting (login, project, credential) VALUES (%s, %s, %s);'
                    cur.executemany(sql, [[user.login, 'cati_portal', 'server_admin'],
                                           [user.login, 'cati_portal', 'user_moderator']])
                flash(f'Administrator {form.login.data} succesfully registered and activated with server and user management rights', 'success')
                user = User.get(user.login)
                login_user(user)
                os.remove(hash_file)
                return redirect(url_for('settings.settings'))
            flash('Invalid installation code', 'danger')
        return render_template('form_page.html', title='Administrator registration', form=form)
    abort(404)

@bp.route('/login', methods=('GET', 'POST'))
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home.index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.get(form.login.data)
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password', 'warning')
            return redirect(url_for('authentication.login'))
        login_user(user)
        return form.redirect('home.index')
    return render_template('form_page.html', form=form, title='Sign in')

@bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home.index'))


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
        return redirect(url_for('home.index'))
    return render_template('form_page.html', form=form)
