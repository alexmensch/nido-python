import json
from numbers import Number
from flask import Flask, request, session, g, render_template, flash
from lib.Nido import Sensor, LocalWeather, Config, Controller, Status, ControllerError
import lib.NidoServer as ns

config = Config()
DEBUG = config.get_config()['flask']['debug']
SECRET_KEY = config.get_config()['flask']['secret_key']
GOOGLE_API_KEY = config.get_config()['google']['api_key']

app = Flask(__name__)
app.config.from_object(__name__)
# Register custom converter with Flask
app.url_map.converters['regex'] = ns.RegexConverter

# Application routes
#   All routes are POST-only and should only return JSON.
#   The / route only serves to return the React-based UI
#
@app.route('/')
def render_ui():
    return render_template('index.html', google_api_key=GOOGLE_API_KEY)

@app.route('/login', methods=['POST'])
def login():
    # Intialize response object
    resp = ns.JSONResponse()
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
            # Default session lifetime is 31 days
            session.permanent = True
            resp.data['logged_in'] = True
            resp.data['message'] = 'User has been logged in.'

    return resp.get_flask_response(app)

@app.route('/logout', methods=['POST'])
def logout():
    # Initialize response object
    resp = ns.JSONResponse()
    if 'logged_in' in session:
        resp.data['message'] = 'User has been logged out.'
        resp.data['username'] = session['username']
        resp.data['logged_in'] = False
        # Note that clear() removes every key from the session dict, which causes the cookie to be destroyed
        session.clear()
    else:
        resp.data['error'] = 'User not logged in.'
        resp.data['logged_in'] = False
    return resp.get_flask_response(app)

@app.route('/get_state', methods=['POST'])
@ns.require_session
def get_state():
    # Initialize response object
    resp = ns.JSONResponse()
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
    return resp.get_flask_response(app)

@app.route('/get_weather', methods=['POST'])
@ns.require_session
def get_weather():
    resp = ns.JSONResponse()

    # Any errors will be passed through
    # The receiving application should note the retrieval_age value as necessary
    # TODO: Support caching built into the LocalWeather() object by storing the object in the session
    #       Needs to be a serializable object (see Flask documentation)
    resp.data = LocalWeather().get_conditions()

    return resp.get_flask_response(app)

@app.route('/get_config', methods=['POST'])
@ns.require_session
def get_config():
    # Initialize response dict
    resp = ns.JSONResponse()
    # Get config
    cfg = config.get_config()
    # Check that settings config section exists
    if 'config' in cfg:
        resp.data['config'] = cfg['config']
    else:
        resp.data['error'] = 'Unable to retrieve config schema.'

    return resp.get_flask_response(app)

@app.route('/set_config', methods=['POST'])
@ns.require_session
def set_config():
    # Initialize response object
    resp = ns.JSONResponse()
    new_cfg = request.get_json()
        
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
    if ns.validate_json_req(new_cfg, validation):
        resp = ns.set_config_helper(resp, cfg=new_cfg)
    else:
        resp.data['error'] = 'JSON in request was invalid.'
        resp.status = 400

    return resp.get_flask_response(app)

# Public API routes
#   Secured by a pre-shared secret key in the request body

# Endpoint to accept a new mode setting.
# Only setting one of the valid configured modes is possible.
#
@app.route('/api/set_mode/<string:set_mode>', methods=['POST'])
@ns.require_secret
def api_set_mode(set_mode):
    resp = ns.JSONResponse()
    resp = ns.set_config_helper(resp, mode=set_mode)
    return resp.get_flask_response(app)

# Endpoint to accept a new set temperature in either Celsius or Fahrenheit.
# The first regex accepts either integer or floating point numbers.
#
@app.route('/api/set_temp/<regex("(([0-9]*)(\.([0-9]+))?)"):temp>/<regex("[cCfF]"):scale>', methods=['POST'])
@ns.require_secret
def api_set_temp(temp, scale):
    # Initialize response object
    resp = ns.JSONResponse()
    temp = float("{0:.1f}".format(float(temp)))
    resp = ns.set_config_helper(resp, temp_scale=[temp, scale])
    return resp.get_flask_response(app)

if __name__ == '__main__':
    # We're using an adhoc SSL context, which is not considered secure by browsers
    # because it invokes a self-signed certificate.
    app.run(host='0.0.0.0', port=config.get_config()['flask']['port'], ssl_context='adhoc', threaded=False)
