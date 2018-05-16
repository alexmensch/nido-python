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

import os
from numbers import Number
from flask import Flask, request, session, render_template
from lib.nido import (Sensor, LocalWeather, Config, Controller, Status,
                      ControllerError)
import lib.nidoserver as ns
from lib.scheduler import NidoDaemonService, NidoDaemonServiceError

config = Config()
if 'NIDO_DEBUG' in os.environ:
    DEBUG = True
else:
    DEBUG = config.get_config()['flask']['debug']
if 'NIDO_TESTING' in os.environ:
    SSL_MODE = None
else:
    SSL_MODE = 'adhoc'
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
        if (request.form['username'] != cfg['flask']['username']
                or request.form['password'] != cfg['flask']['password']):
            resp.data['error'] = 'Incorrect login credentials.'
            resp.data['logged_in'] = False
        else:
            # Set (implicit create) session cookie (HTTP only) which all
            # endpoints will check for
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
        # Note that clear() removes every key from the session dict,
        # which causes the cookie to be destroyed
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
        err_msg = 'Exception getting current state from controller: {}' \
                  .format(str(e))
        resp.data['error'].append(err_msg)
    else:
        # state = Heating / Cooling / Off
        nidoState = {'status': Status(state).name}
        resp.data['state'].update(nidoState)

    # Returns a JSON dict with an 'error' key on error
    # On success, returns a JSON dict with a 'conditions' key
    sensor_data = Sensor().get_conditions()
    if 'error' in sensor_data:
        resp.data['error'].append(sensor_data['error'])
    else:
        resp.data['state'].update(sensor_data)

    daemonState = {'daemon_running': Controller().daemon_running()}
    resp.data['state'].update(daemonState)

    if len(resp.data['error']) == 0:
        del resp.data['error']
    return resp.get_flask_response(app)

@app.route('/get_weather', methods=['POST'])
@ns.require_session
def get_weather():
    resp = ns.JSONResponse()
    # Any errors will be passed through
    # The receiving application should note the retrieval_age value
    # as necessary.
    # TODO: Support caching built into the LocalWeather() object by
    #       storing the object in the session.
    #       Needs to be a serializable object (see Flask documentation).
    resp.data = LocalWeather().get_conditions()

    return resp.get_flask_response(app)

@app.route('/get_config', methods=['POST'])
@ns.require_session
def get_config():
    resp = ns.JSONResponse()
    cfg = config.get_config()
    resp.data['config'] = cfg['config']
    return resp.get_flask_response(app)

@app.route('/set_config', methods=['POST'])
@ns.require_session
def set_config():
    resp = ns.JSONResponse()
    new_cfg = request.get_json()

    # Expect to receive a json dict with
    # one or more of the following pairs
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

@app.route('/api/set/mode/<string:set_mode>', methods=['POST'])
@ns.require_secret
def api_set_mode(set_mode):
    """Endpoint to accept a new mode setting.

    Only setting one of the valid configured modes is possible.
    """

    resp = ns.JSONResponse()
    resp = ns.set_config_helper(resp, mode=set_mode)
    return resp.get_flask_response(app)

@app.route('/api/set/temp/<regex("(([0-9]*)(\.([0-9]+))?)"):temp> \
            /<regex("[cCfF]"):scale>', methods=['POST'])
@ns.require_secret
def api_set_temp(temp, scale):
    """Endpoint to accept a new set temperature in either
    Celsius or Fahrenheit.

    The first regex accepts either integer or floating point numbers.
    """

    resp = ns.JSONResponse()
    temp = float("{:.1f}".format(float(temp)))
    resp = ns.set_config_helper(resp, temp_scale=[temp, scale])
    return resp.get_flask_response(app)

@app.route('/api/schedule/get/all', methods=['POST'])
@ns.require_secret
def api_schedule_get_all():
    """Endpoint that returns all jobs in the scheduler."""

    resp = ns.JSONResponse()
    nds = NidoDaemonService(json=True)
    resp.data['jobs'] = nds.get_scheduled_jobs()
    return resp.get_flask_response(app)

@app.route('/api/schedule/get/<string:id>', methods=['POST'])
@ns.require_secret
def api_schedule_get_jobid(id):
    """Endpoint that returns a scheduled job with a specific id."""

    resp = ns.JSONResponse()
    nds = NidoDaemonService(json=True)
    try:
        resp.data['job'] = nds.get_scheduled_job(id)
    except NidoDaemonServiceError as e:
        resp.data['error'] = 'Error getting job: {}'.format(e)
    return resp.get_flask_response(app)

@app.route('/api/schedule/add/<string:type>', methods=['POST'])
@ns.require_secret
def api_schedule_add_job(type):
    """Endpoint to add a new, persistent scheduled job.

    The 'type' value in the URL must be either "temp" or "mode".
    The body must consist of a JSON object with the following
    valid keys:
        Job type-specific:
            mode -> What mode should be triggered (off, heat, cool)
            temp -> What temperature should be triggered (float value)
            scale -> What temperature scale the temp is in ("C" or "F")
        Combination of cron-style timing options (supplying at least
        one of the following is required):
            day_of_week -> Specify the day(s) of the week that the job
                           should be triggered
            hour -> Specify the hour(s) that the job should be triggered
            minute -> Specify the minute(s) that the job
                      should be triggered
        Optional:
            job_id -> Specify a job ID for the job
    """

    resp = ns.JSONResponse()
    nds = NidoDaemonService(json=True)

    job_kwargs = request.get_json()
    del job_kwargs['secret']

    if type.lower() == 'mode' or type.lower() == 'temp':
        try:
            resp.data['job'] = nds.add_scheduled_job(type, **job_kwargs)
        except NidoDaemonServiceError as e:
            resp.data['error'] = 'Error adding job: {}'.format(e)
    else:
        resp.data['error'] = 'Invalid mode specified.'    
        resp.status = 400

    return resp.get_flask_response(app)

@app.route('/api/schedule/modify/<string:id>', methods=['POST'])
@ns.require_secret
def api_schedule_modify_jobid(id):
    """Endpoint to modify the job parameters of a scheduled job.

    The 'id' value in the URL must be the ID of an existing
    scheduled job.
    The body must consist of a JSON object with the following
    valid keys depending on the job type:
        Job type:
            type -> "mode" or "temp"
        "mode" type:
            mode -> What mode should be triggered (off, heat, cool)
        "temp" type:
            temp -> What temperature should be triggered (float value)
            scale -> What temperature scale the temp is in ("C" or "F")
    """

    resp = ns.JSONResponse()
    nds = NidoDaemonService(json=True)

    job_kwargs = request.get_json()
    del job_kwargs['secret']

    try:
        resp.data['job'] = nds.modify_scheduled_job(id, **job_kwargs)
    except NidoDaemonServiceError as e:
        resp.data['error'] = 'Error modifying job ID ({}): {}'.format(id, e)

    return resp.get_flask_response(app)

@app.route('/api/schedule/reschedule/<string:id>', methods=['POST'])
@ns.require_secret
def api_schedule_reschedule_jobid(id):
    """Endpoint to modify the schedule of a scheduled job.

    The 'id' value in the URL must be the ID of an existing
    scheduled job.
    The body must consist of a JSON object with the following
    valid keys depending on the job type:
        Combination of cron-style timing options (supplying at least
        one of the following is required):
            day_of_week -> Specify the day(s) of the week that the job
                           should be triggered
            hour -> Specify the hour(s) that the job should be triggered
            minute -> Specify the minute(s) that the job
                      should be triggered
    """

    resp = ns.JSONResponse()
    nds = NidoDaemonService(json=True)

    job_kwargs = request.get_json()
    del job_kwargs['secret']

    try:
        resp.data['job'] = nds.reschedule_job(id, **job_kwargs)
    except NidoDaemonServiceError as e:
        resp.data['error'] = 'Error rescheduling job ID ({}): {}'.format(id, e)

    return resp.get_flask_response(app)

@app.route('/api/schedule/pause/<string:id>', methods=['POST'])
@ns.require_secret
def api_schedule_pause_jobid(id):
    resp = ns.JSONResponse()
    nds = NidoDaemonService(json=True)
    try:
        resp.data['job'] = nds.pause_scheduled_job(id)
    except NidoDaemonServiceError as e:
        resp.data['error'] = 'Error pausing job: {}'.format(e)
    return resp.get_flask_response(app)

@app.route('/api/schedule/resume/<string:id>', methods=['POST'])
@ns.require_secret
def api_schedule_resume_jobid(id):
    resp = ns.JSONResponse()
    nds = NidoDaemonService(json=True)
    try:
        resp.data['job'] = nds.resume_scheduled_job(id)
    except NidoDaemonServiceError as e:
        resp.data['error'] = 'Error resuming job: {}'.format(e)
    return resp.get_flask_response(app)

@app.route('/api/schedule/remove/<string:id>', methods=['POST'])
@ns.require_secret
def api_schedule_remove_jobid(id):
    resp = ns.JSONResponse()
    nds = NidoDaemonService(json=True)
    try:
        resp.data['job'] = nds.remove_scheduled_job(id)
    except NidoDaemonServiceError as e:
        resp.data['error'] = 'Error removing job: {}'.format(e)
    return resp.get_flask_response(app)


if __name__ == '__main__':
    # We're using an adhoc SSL context, which is not considered secure
    # by browsers because it invokes a self-signed certificate.
    app.run(host='0.0.0.0', port=config.get_config()['flask']['port'],
            ssl_context=SSL_MODE, threaded=False)
