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
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.

import json
from flask import session, abort, request
from werkzeug.routing import BaseConverter
from functools import wraps
from Nido import Config, ConfigError, Controller
from Scheduler import NidoDaemonService

config = Config()
PUBLIC_API_SECRET = config.get_config()['flask']['public_api_secret']

# JSON response object
#
class JSONResponse:
    def __init__(self):
        self.status = 200
        self.data = {
                'version': config.get_version()
                }
        return

    def get_flask_response(self, app):
        response = app.make_response(json.dumps(self.data))
        response.headers['Content-Type'] = 'application/json'
        response.status_code = self.status
        return response

# Helper function to validate JSON in requests
# A list of tuples is passed in of the form ( 'name', type )
# Where:
#        'name' is the key we expect in the dict
#        type is a type we can compare the corresponding value to using isinstance()
###
# TODO: Improve validation
#       eg. location should be a list of only two numbers
#       eg. modes_available be a list of lists, each with only two values
def validate_json_req(req_data, valid):
    # Make sure we have JSON in the body first
    if (req_data == None) or (req_data == {}):
        return False

    # Request data can't have more entries than the validation set
    if len(valid.keys()) < len(req_data.keys()):
        print 'Bad length'
        return False

    # Check that each element in the request data is valid
    for setting in req_data:
        if setting not in valid:
            print 'Setting name is not in valid dict'
            return False
        elif not isinstance(req_data[setting], valid[setting]):
            print 'Setting value is not instance of valid type'
            print 'setting: {}, type: {}'.format(req_data[setting], type(req_data[setting]))
            print 'valid type: {}'.format(valid[setting])
            return False

    # No tests failed
    return True

# Helper function to set config
def set_config_helper(resp, cfg=None, mode=None, temp_scale=None):
    if mode:
        if config.set_mode(mode):
            resp.data['message'] = 'Mode updated successfully.'
        else:
            resp.data['error'] = 'Invalid mode.'
            resp.status = 400
    elif temp_scale:
        if config.set_temp(temp_scale[0], temp_scale[1]):
            resp.data['message'] = 'Temperature updated successfully.'
        else:
            resp.data['error'] = 'Invalid temperature.'
            resp.status = 400
    elif cfg:
        if config.update_config(cfg):
            resp.data['message'] = 'Configuration updated successfully.'
        else:
            resp.data['error'] = 'Invalid configuration setting(s).'
            resp.status = 400
    else:
        raise ConfigError('No configuration setting specified.')

    resp.data['config'] = config.get_config()['config']

    # Send signal to daemon, if running, to trigger update
    try:
        NidoDaemonService().wakeup()
    except Exception as e:
        resp.data['warning'] = 'Server error signalling daemon: {}'.format(e)
    return resp

# Decorator for routes that require a session cookie
#
def require_session(route):
    @wraps(route)
    def check_session(*args, **kwargs):
        if not session.get('logged_in'):
            abort(403)
        else:
            return route(*args, **kwargs)

    return check_session

# Decorator for API routes to verify that client supplied a secret in the request body
#
def require_secret(route):
    @wraps(route)
    def check_secret(*args, **kwargs):
        req_data = request.get_json()
        # Prepare a JSONResponse in case we need it
        resp = JSONResponse()

        if 'secret' in req_data.keys():
            if req_data['secret'] == PUBLIC_API_SECRET:
                return route(*args, **kwargs)
            else:
                resp.data['error'] = 'Invalid secret.'
                resp.status = 401
        else:
            resp.data['error'] = 'JSON in request was invalid.'
            resp.status = 400

        return resp.get_flask_response()

    return check_secret

# Custom URL converter to allow use of regex
# Source: https://stackoverflow.com/questions/5870188/does-flask-support-regular-expressions-in-its-url-routing
#
class RegexConverter(BaseConverter):
    def __init__(self, url_map, *items):
        super(RegexConverter, self).__init__(url_map)
        self.regex = items[0]
