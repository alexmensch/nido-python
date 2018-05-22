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
from flask import Blueprint, current_app, request, g
from werkzeug.routing import BaseConverter
from nido.lib.nidoserver import JSONResponse
from nido.lib.scheduler import NidoDaemonService

bp = Blueprint('api', __name__)


def require_secret(route):
    """Decorator for API routes to verify that client supplied a secret
    in the request body.
    """
    @wraps(route)
    def check_secret(*args, **kwargs):
        req_data = request.get_json()
        # Prepare a JSONResponse in case we need it
        resp = JSONResponse()

        if 'secret' in list(req_data.keys()):
            if req_data['secret'] == current_app.config['PUBLIC_API_SECRET']:
                return route(*args, **kwargs)
            else:
                resp.data['error'] = 'Invalid secret.'
                resp.status = 401
        else:
            resp.data['error'] = 'JSON in request was invalid.'
            resp.status = 400

        return resp.get_flask_response()

    return check_secret


@bp.before_app_request
def json_response():
    g.resp = JSONResponse()
    g.nds = NidoDaemonService(json=True)
    return None


# Custom URL converter to allow use of regex
# Source: https://stackoverflow.com/questions/5870188 \
# /does-flask-support-regular-expressions-in-its-url-routing
#
class RegexConverter(BaseConverter):
    """Custom URL converter to allow use of regular expressions.
    Source: https://stackoverflow.com/questions/5870188\
    /does-flask-support-regular-expressions-in-its-url-routing
    """
    def __init__(self, url_map, *items):
        super(RegexConverter, self).__init__(url_map)
        self.regex = items[0]
