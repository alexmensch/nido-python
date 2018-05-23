#   Nido, a Raspberry Pi-based home thermostat.
#
#   Copyright (C) 2016 Alex Marshall
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program.
#   If not, see <http://www.gnu.org/licenses/>.

from functools import wraps
from flask import Blueprint, session, current_app, request, abort, g

from nido.api import JSONResponse

bp = Blueprint('auth', __name__)


def require_session(route):
    """Decorator for routes that require a session cookie."""
    @wraps(route)
    def check_session(*args, **kwargs):
        if not session.get('logged_in'):
            abort(403)
        else:
            return route(*args, **kwargs)

    return check_session


@bp.before_app_request
def json_response():
    g.resp = JSONResponse()
    return None


@bp.route('/login', methods=['POST'])
def login():
    if 'logged_in' in session:
        g.resp.data['message'] = 'User already logged in.'
        g.resp.data['username'] = session['username']
        g.resp.data['logged_in'] = True
    else:
        USERNAME = current_app.config['USERNAME']
        PASSWORD = current_app.config['PASSWORD']
        if (request.form['username'] != USERNAME
                or request.form['password'] != PASSWORD):
            g.resp.data['error'] = 'Incorrect login credentials.'
            g.resp.data['logged_in'] = False
        else:
            # Set (implicit create) session cookie (HTTP only) which all
            # endpoints will check for
            session['logged_in'] = True
            session['username'] = request.form['username']
            # Default session lifetime is 31 days
            session.permanent = True
            g.resp.data['logged_in'] = True
            g.resp.data['message'] = 'User has been logged in.'

    return g.resp.get_flask_response(current_app)


@bp.route('/logout', methods=['POST'])
def logout():
    if 'logged_in' in session:
        g.resp.data['message'] = 'User has been logged out.'
        g.resp.data['username'] = session['username']
        g.resp.data['logged_in'] = False
        # Note that clear() removes every key from the session dict,
        # which causes the cookie to be destroyed
        session.clear()
    else:
        g.resp.data['error'] = 'User not logged in.'
        g.resp.data['logged_in'] = False
    return g.resp.get_flask_response(current_app)
