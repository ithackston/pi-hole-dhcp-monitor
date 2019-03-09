import functools
from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from werkzeug.security import check_password_hash, generate_password_hash
from simplepam import authenticate

bp = Blueprint('auth', __name__)

@bp.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        error = None

        if authenticate(str(username), str(password)):
            session.clear()
            session['logged_in'] = True
            return redirect(url_for('index'))
        else:
            flash('Invalid credentials.')

    return render_template('auth/login.html')


@bp.before_app_request
def load_logged_in_user():
    g.logged_in = session.get('logged_in', False)


def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if not session.get('logged_in', False):
            return redirect(url_for('auth.login'))

        return view(**kwargs)

    return wrapped_view


@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.login'))
