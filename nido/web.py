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
from .lib.nidoserver import JSONResponse
from .lib.nido import Config

bp = Blueprint('auth', __name__)


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
        err_msg = (
            'Exception getting current state from controller: {}'
            .format(str(e))
        )
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