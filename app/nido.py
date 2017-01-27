import json
from numbers import Number
from functools import wraps
from flask import Flask, request, session, g, redirect, url_for, abort, render_template, flash
from lib.Nido import Sensor, LocalWeather, Config, Controller, Status, ControllerError, ConfigError

# Configuration
config = Config()
# Validate configuration file before we continue
if config.validate() == False:
    exit('Error: incomplete configuration, please verify config.yaml settings.')
DEBUG = config.get_config()['flask']['debug']
SECRET_KEY = config.get_config()['flask']['secret_key']

# Initialize the application
#
app = Flask(__name__)
app.config.from_object(__name__)

# JSON response object
#
class JSONResponse():
    def __init__(self):
        self.status = 200
        self.data = {
                'version': config.get_version()
                }
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

# Helper function to update config settings
def update_config(old_cfg, new_cfg):
    cfg = old_cfg

    for setting in new_cfg:
        if setting == 'modes_available':
            cfg['modes'] = config.list_modes(new_cfg[setting])
        cfg[setting] = new_cfg[setting]

    return cfg

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

# Application routes
#   All routes are POST-only and should only return JSON.
#   The / route only serves to return the React-based UI
#
@app.route('/set_config', methods=['POST'])
@require_session
def set_config():
    # Initialize response object
    resp = JSONResponse()
    new_cfg = request.get_json()
    # Make sure we received JSON
    if new_cfg == None:
        resp.data['error'] = 'Empty request body.'
        resp.status = 400
    elif new_cfg == {}:
        resp.data['error'] = 'Empty JSON request received.'
        resp.status = 400
    else:
        # Expect to receive a json dict with one or more of the following pairs
        # TODO: Improve validation
        #       eg. location should be a list of only two numbers
        #       eg. modes_available be a list of lists, each with only two values
        validation = {
            'location': list,
            'celsius': bool,
            'modes_available': list,
            'mode_set': basestring,
            'set_temperature': Number
            }
        # Update local configuration with user data
        if validate_json_req(request, validation):
            cfg = config.get_config()
            cfg['config'] = update_config(cfg['config'], new_cfg)
            try:
                config.set_config(cfg)
            except ConfigError as e:
                resp.data['error'] = 'Server error updating configuration: {}'.format(e)
            else:
                resp.data['message'] = 'Configuration updated successfully.'
                resp.data['config'] = cfg['config']
                # Send signal to daemon, if running, to trigger update
                try:
                    Controller().signal_daemon()
                except ControllerError as e:
                    resp.data['error'] = 'Server error signaling daemon: {}'.format(e)
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
    if 'config' in cfg:
        resp.data['config'] = cfg['config']
    else:
        resp.data['error'] = 'Unable to retrieve config schema.'

    return resp.get_flask_response()

@app.route('/')
def render_ui():
    return render_template('index.html')

@app.route('/get_state', methods=['POST'])
@require_session
def get_state():
    # Initialize response object
    resp = JSONResponse()
    resp.data['state'] = {}
    resp.data['error'] = []
    
    try:
        state = Controller().get_status()
    except ControllerError as e:
        err_msg = 'Exception getting current state from controller: {}'.format(str(e))
        resp.data['error'].append(err_msg)
    else:
        # state = Heating / Cooling / Off
        nidoState = { 'status': Status(state).name }
        resp.data['state'].update(nidoState)
        
    # Returns a JSON dict with an 'error' key on error
    # On success, returns a JSON dict with a 'conditions' key
    sensor_data = Sensor().get_conditions()
    if 'error' in sensor_data:
        resp.data['error'].append(sensor_data['error'])
    else:
        resp.data['state'].update(sensor_data)

    daemonState = { 'daemon_running': Controller().daemon_running() }
    resp.data['state'].update(daemonState)

    if len(resp.data['error']) == 0:
        del resp.data['error']
    return resp.get_flask_response()

@app.route('/get_weather', methods=['POST'])
def get_weather():
    resp = JSONResponse()

    # Any errors will be passed through
    # The receiving application should note the retrieval_age value as necessary
    # TODO: Support caching built into the LocalWeather() object by storing the object in the session
    #       Needs to be a serializable object (see Flask documentation)
    resp.data = LocalWeather().get_conditions()

    return resp.get_flask_response()

@app.route('/login', methods=['POST'])
def login():
    # Intialize response object
    resp = JSONResponse()
    # Get config
    cfg = config.get_config()
    
    if 'logged_in' in session:
        resp.data['message'] = 'User already logged in.'
        resp.data['username'] = session['username']
        resp.data['logged_in'] = True
    else:
        if request.form['username'] != cfg['flask']['username'] or request.form['password'] != cfg['flask']['password']:
            resp.data['error'] = 'Incorrect login credentials.'
            resp.data['logged_in'] = False
        else:
            # Set (implicit create) session cookie (HTTP only) which all endpoints will check for
            session['logged_in'] = True
            session['username'] = request.form['username']
            resp.data['logged_in'] = True
            resp.data['message'] = 'User has been logged in.'

    return resp.get_flask_response()

@app.route('/logout', methods=['POST'])
def logout():
    # Initialize response object
    resp = JSONResponse()
    if 'logged_in' in session:
        resp.data['message'] = 'User has been logged out.'
        resp.data['username'] = session['username']
        resp.data['logged_in'] = False
        # Note that clear() removes every key from the session dict, which causes the cookie to be destroyed
        session.clear()
    else:
        resp.data['error'] = 'User not logged in.'
        resp.data['logged_in'] = False
    return resp.get_flask_response()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=config.get_config()['flask']['port'])
