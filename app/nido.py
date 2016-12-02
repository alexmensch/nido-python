import json
from numbers import Number
from contextlib import closing
from enum import Enum
from flask import Flask, request, session, g, redirect, url_for, abort, render_template, flash
from validate_email import validate_email
from lib.CollectData import Sensor, LocalWeather
from lib.NidoConfig import NidoConfig

# Configuration
config = NidoConfig()
DEBUG = config.get_config()['flask']['debug']
SECRET_KEY = config.get_config()['flask']['secret_key']

# Initialize the application
#
app = Flask(__name__)
app.config.from_object(__name__)

# Define some enums
#
class Mode(Enum):
    off = 0
    heat = 1
    cool = 2
    heat_cool = 3

_MODE_NAME = {
        Mode.off: 'Off',
        Mode.heat: 'Heat',
        Mode.cool: 'Cool',
        Mode.heat_cool: 'Heat/Cool'
        }

class Status(Enum):
    off = 0
    heating = 1
    cooling = 2

_STATUS_NAME = {
        Status.off: 'Off',
        Status.heating: 'Heating',
        Status.cooling: 'Cooling'
        }

# JSON response object
#
class JSONResponse():
    def __init__(self):
        self.status = 200
        self.data = {}
        return

    def get_flask_response(self):
        response = app.make_response(json.dumps(self.data))
        response.headers['Content-Type'] = 'application/json'
        response.status_code = self.status
        return response

# Helper function to validate JSON in requests
# A list of tuples is passed in of the form ( 'name', type )
# Where:
#        'name' is the key we expect in the dict
#        type is a type we can compare the corresponding value to using isinstance()
def validate_json_req(req, valid):
    # Get the JSON from the request object
    req_data = req.get_json()

    # Number of elements must match
    if len(valid) != len(req_data.keys()):
        return false

    # Check that each element in the valid list exists and that the type matches
    for i in valid:
        if i[0] not in req_data:
            return false
        if not isinstance(req_data[i[0]], i[1]):
            return false

    # No tests failed
    return true

# Decorator for routes that require a session cookie
#
def require_session(route):
    def check_session(self, *args, **kwargs):
        if not session.get('logged_in'):
            abort(403)
        else:
            return route(self, *args, **kwargs)

    return check_session

# Application routes
#   All routes are POST-only and should only return JSON.
#   The / route only serves to return the React-based UI
#
@app.route('/set_config', methods=['POST'])
@require_session
def set_config():
    # Initialize response object
    resp = JSONResponse()
    # Make sure we received JSON
    if request.get_json() is None:
        resp.data['error'] = 'Did not receive a JSON request. Check MIME type and request body.'
        resp.status = 400
    else:
        # Expect to receive a json dict with following structure
        validation = [
                ( 'location', [Number, Number] ),
                ( 'location_name', basestring ),
                ( 'nido_location', basestring ),
                ( 'celsius', bool ),
                ( 'mode', Number ),
                ( 'set_temperature', Number )
                ]
        # Update local configuration with user data
        if validate_json_req(request, validation):
            cfg = config.get_config()
            cfg['settings'] = request.get_json()
            try:
                config.set_config(cfg)
            except:
                raise
            else:
                resp.data['message'] = 'Settings updated successfully.'
        else:
            resp.data['error'] = 'JSON in request was invalid.'

    return resp.get_flask_response()

@app.route('/get_config', methods=['POST'])
@require_session
def get_config():
    # Initialize response dict
    resp = JSONResponse()
    # Get config
    cfg = config.get_config()
    # Check that settings config section exists
    if 'settings' in cfg:
        resp.data['settings'] = cfg['settings']
    else:
        resp.data['error'] = 'No settings available.'

    return resp.get_flask_response()

@app.route('/add_user', methods=['POST'])
@require_session
def add_user():
    # Initialize response dict
    resp = JSONResponse()
    # Make sure we received JSON
    if request.get_json() is None:
        resp.data['error'] = 'Did not receive a JSON request. Check MIME type and request body.'
        resp.status = 400
    else:
        # Expect to receive a json dict with following structure
        validation = [
                ( 'name_first', basestring ),
                ( 'name_last', basestring ),
                ( 'email', basestring )
                ]
        # Update local configuration with user data
        if validate_json_req(request, validation):
            cfg = config.get_config()
            cfg['user'] = request.get_json()
            try:
                config.set_config(cfg)
            except:
                raise
            else:
                resp.data['message'] = 'User added successfully.'
        else:
            resp.data['error'] = 'JSON in request was invalid.'

    return resp.get_flask_response()

@app.route('/')
def render_ui():
    return render_template('index.html')

@app.route('/get_state', methods=['POST'])
@require_session
def get_state():
    # Initialize response object
    resp = JSONResponse()
    # Get config
    cfg = config.get_config()
    
    # Check if settings are available
    if 'settings' in cfg:
        # Return current settings
        resp.data['settings'] = cfg['settings']
        try:
            # TODO: Pull state from Controller object
            # resp.data['state'] = ...
            pass
        except:
            raise
    else:
        resp.data['error'] = 'No settings. Has Nido been configured yet?'

    return resp.get_flask_response()

@app.route('/login', methods=['POST'])
def login():
    # Intialize response object
    resp = JSONResponse()
    # Get config
    cfg = config.get_config()
    
    if 'logged_in' in session:
        try:
            resp.data['message'] = 'User already logged in.'
            resp.data['username'] = session['username']
            resp.data['logged_in'] = True
        except:
            raise
    else:
        try:
            if request.form['username'] != cfg['flask']['username'] or request.form['password'] != cfg['flask']['password']:
                resp.data['error'] = 'Incorrect login credentials.'
                resp.data['logged_in'] = False
            else:
                # Set (implicit create) session cookie (HTTP only) which all endpoints will check for
                session['logged_in'] = True
                session['username'] = request.form['username']
                resp.data['message'] = 'User has been logged in.'
                resp.data['username'] = request.form['username']
                resp.data['logged_in'] = True
        except:
            raise

    return resp.get_flask_response()

@app.route('/logout', methods=['POST'])
def logout():
    # Initialize response object
    resp = JSONResponse()
    if 'logged_in' in session:
        try:
            resp.data['message'] = 'User has been logged out.'
            resp.data['username'] = session['username']
            resp.data['logged_in'] = False
            # Note that clear() removes every key from the session dict, which causes the cookie to be destroyed
            session.clear()
        except:
            raise
    else:
        resp.data['error'] = 'User not logged in.'
        resp.data['logged_in'] = False
    return json_response(resp)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=config.get_config()['flask']['port'])
