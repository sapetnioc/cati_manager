import base64
import datetime
from functools import wraps
import os
import os.path as osp
import uuid

from flask import (Blueprint, render_template, url_for, redirect, flash,
                   abort, request)
from flask_wtf import FlaskForm
from flask_login import current_user, login_user, login_required, logout_user
import pgpy
from wtforms import StringField, PasswordField, HiddenField, SubmitField, validators
from wtforms.widgets import HiddenInput

from cati_portal.db import _get_admin_cursor, get_cursor
from cati_portal.encryption import hash_password, check_password
from cati_portal.form import RedirectForm


def credential_required(credential):
    def decorator(func):
        @wraps(func)
        def decorated_view(*args, **kwargs):
            if not current_user.has_credential(credential):
                return current_app.login_manager.unauthorized()
            return func(*args, **kwargs)

        return login_required(decorated_view)
    return decorator

bp = Blueprint('authentication', __name__, url_prefix='/authentication')


class LoginForm(RedirectForm):
    login = StringField('login', [validators.DataRequired()])
    password = PasswordField('Password', validators=[validators.DataRequired()])
    submit = SubmitField('Sign in')


class User:
    def __init__(self, login, email, first_name, last_name, institution,
                 registration_time, email_verification_time,
                 email_verification_code, activation_time,
                 deactivation_time):
        self.login = login
        self.email_verification_time = email_verification_time
        if email_verification_code:
            self.email_verification_code = email_verification_code
        self.email = email
        self.first_name = first_name
        self.last_name = last_name
        self.institution = institution
        self.registration_time = registration_time
        self.activation_time = activation_time
        self.deactivation_time = deactivation_time
        self.is_active = (activation_time is not None and
                          email_verification_time is not None and
                          deactivation_time is None)
        self.is_authenticated = True
        self.is_anonymous = False

    @staticmethod
    def _iterate_users(cur, where, where_data):
        sql = f'SELECT login, email, first_name, last_name, institution, registration_time, email_verification_time, activation_time, deactivation_time FROM cati_portal.identity WHERE {where}'
        cur.execute(sql, where_data)
        for row in cur:
            login, email, first_name, last_name, institution, registration_time, email_verification_time, activation_time, deactivation_time = row
            if email_verification_time is None:
                email_verification_code, email = email.split(':', 1)
            else:
                email_verification_code = None
            yield User(login=login,
                       email=email,
                       first_name=first_name,
                       last_name=last_name,
                       institution=institution,
                       registration_time=registration_time,
                       email_verification_time=email_verification_time,
                       email_verification_code=email_verification_code,
                       activation_time=activation_time,
                       deactivation_time=deactivation_time)

    @staticmethod
    def get(login, bypass_access_rights=False):
        if bypass_access_rights:
            cursor_factory = _get_admin_cursor
        else:
            cursor_factory = get_cursor
        with cursor_factory() as cur:
            user_generator = User._iterate_users(cur, 'login = %s', [login])
            try:
                return next(user_generator)
            except StopIteration:
                pass
        return None

    @staticmethod
    def get_from_email_verification_code(email_verification_code):
        with _get_admin_cursor() as cur:
            user_generator = User._iterate_users(cur, 'email LIKE %s', [f'{email_verification_code}:%'])
            try:
                return next(user_generator)
            except StopIteration:
                pass
        return None

    @staticmethod
    def create(login, password, email, first_name=None, last_name=None, institution=None):
        '''
        Create a new user in the database
        '''
        with _get_admin_cursor() as cur:
            email_verification_code = str(uuid.uuid4())
            email = f'{email_verification_code}:{email}'
            sql = 'INSERT INTO cati_portal.identity(login, password, email, first_name, last_name, institution) VALUES (%s, %s, %s, %s, %s, %s)'
            cur.execute(sql, [login, password, email, first_name, last_name, institution])
        return User.get(login, bypass_access_rights=True)

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


class Users:
    @staticmethod
    def list():
        with get_cursor() as cur:
            for user in User._iterate_users(cur, 'TRUE', []):
                yield user


@bp.route('/install', methods=('GET', 'POST'))
def install():
    hash_file = osp.join(os.environ.get('CATI_PORTAL_DIR', '/cati_portal'), 'tmp', 'installation.hash')
    if osp.exists(hash_file):
        form = RegistrationForm()
        if form.validate_on_submit():
            hash = open(hash_file, 'rb').read()
            if check_password(form.install_code.data, hash):
                user = User.create(login=form.login.data,
                                   email=form.email.data,
                                   password=form.password.data,
                                   first_name=form.first_name.data,
                                   last_name=form.last_name.data,
                                   institution=form.institution.data)
                with _get_admin_cursor() as cur:
                    time = datetime.datetime.now()
                    sql = 'UPDATE cati_portal.identity SET activation_time = %s, email=%s, email_verification_time = %s WHERE login = %s;'
                    cur.execute(sql, [time, user.email, time, user.login])
                    sql = 'INSERT INTO cati_portal.granting (login, project, credential) VALUES (%s, %s, %s);'
                    cur.executemany(sql, [[user.login, 'cati_portal', 'server_admin'],
                                          [user.login, 'cati_portal', 'user_moderator']])
                flash(f'Administrator {form.login.data} succesfully registered and activated with server and user management rights', 'success')
                user = User.get(user.login, bypass_access_rights=True)
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
        user = User.get(form.login.data, bypass_access_rights=True)
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password', 'warning')
            return redirect(url_for('authentication.login'))
        if not user.is_active:
            flash('Account is not activated', 'warning')
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
    login = StringField('login', [validators.DataRequired(), validators.Length(min=4, max=25)], render_kw=dict(size=32))
    email = StringField('Email Address', [validators.DataRequired(), validators.Email()])
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
        user = User.create(login=form.login.data,
                           email=form.email.data,
                           password=form.password.data,
                           first_name=form.first_name.data,
                           last_name=form.last_name.data,
                           institution=form.institution.data)
        flash(f'Succesful registration request for {form.login.data}. An email will be send to {form.email.data} to validate the email. The account must be activated before it can be used.', 'success')
        return redirect(url_for('home.index'))
    return render_template('form_page.html', form=form)


@bp.route('/user/<login>', methods=('DELETE',))
@credential_required('cati_portal.user_moderator')
def delete_user(login):
    with get_cursor() as cur:
        sql = 'DELETE FROM cati_portal.identity WHERE login = %s;'
        cur.execute(sql, [login])
    return ''


@bp.route('/user/<login>', methods=('PUT',))
@credential_required('cati_portal.user_moderator')
def modify_user(login):
    user = User.get(login)
    if user is None:
        abort(404)
    email_verification = request.form.get('email_verification')
    activation = request.form.get('activation')
    deactivation = request.form.get('deactivation')

    user_modifications = {}
    now = datetime.datetime.now()
    if email_verification is not None:
        email_verification = email_verification.lower()
        if email_verification == 'false':
            if user.email_verification_time:
                email_verification_code = str(uuid.uuid4())
                user_modifications['email_verification_time'] = None
                user_modifications['email'] = f'{email_verification_code}:{user.email}'
        elif email_verification == 'true':
            user_modifications['email_verification_time'] = now
            if not user.email_verification_time:
                user_modifications['email'] = user.email
        else:
            abort(400)
    if activation is not None:
        activation = activation.lower()
        if activation == 'false':
            user_modifications['activation_time'] = None
        elif activation == 'true':
            user_modifications['activation_time'] = now
        else:
            abort(400)
    if deactivation is not None:
        deactivation = deactivation.lower()
        if deactivation == 'false':
            user_modifications['deactivation_time'] = None
        elif deactivation == 'true':
            user_modifications['deactivation_time'] = now
        else:
            abort(400)
    if user_modifications:
        with get_cursor() as cur:
            sql_set = ', '.join(f'{col} = %s' for col in user_modifications)
            sql = f'UPDATE cati_portal.identity SET {sql_set} WHERE login = %s;'
            sql_values = list(user_modifications.values())
            sql_values.append(login)
            cur.execute(sql, sql_values)
    else:
        flash(f'Nothing to do', 'danger')
    return ''


@bp.route('/user/<login>/ask_email_validation', methods=('GET',))
@credential_required('cati_portal.user_moderator')
def ask_email_validation(login):
    user = User.get(login)
    if user is None:
        abort(404)
    if user.email_verification_time:
        abort(410)
    url = url_for('authentication.validate_email', code=user.email_verification_code)
    flash(f'Visit <a href="{url}">{url}</a> to validate {login} email.', 'success')
    return ''


@bp.route('/validate_email/<code>', methods=('GET',))
def validate_email(code):
    user = User.get_from_email_verification_code(code)
    if user is not None:
        with _get_admin_cursor() as cur:
            now = datetime.datetime.now()
            sql = 'UPDATE cati_portal.identity SET email = %s, email_verification_time = %s WHERE login = %s;'
            cur.execute(sql, [user.email, now, user.login])
        flash(f'Succesfully validated email for {user.login}', 'success')
        return redirect(url_for('home.index'))
    abort(404)


@bp.route('/users', methods=('GET',))
@credential_required('cati_portal.user_moderator')
def users():
    return render_template('users.html', users=Users(), the_title='Users administration')
