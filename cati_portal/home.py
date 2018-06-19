from flask import Blueprint, render_template

from . import db

bp = Blueprint('home', __name__, url_prefix='/')

@bp.route('')
def main():
    return render_template('home.html')
    #with db.get_cursor() as cur:
        #cur.execute('SELECT * FROM cati_portal.identity;')
        #return str(cur.fetchall())

@bp.route('/login')
def login():
    return render_template('home.html', title='Login')


@bp.route('/register')
def register():
    return render_template('home.html', title='Login')
