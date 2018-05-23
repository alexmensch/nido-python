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

from builtins import str
from past.builtins import basestring

from numbers import Number
import logging
from flask import Blueprint, current_app, g, request

from nido.auth import require_session
from nido.web import LocalWeather, set_config_helper, validate_json_req
from nido.api import JSONResponse
from nido.lib.hardware import (
    Status, Controller, ControllerError, Sensor, Config
)

bp = Blueprint('web_api', __name__)


@bp.before_app_request
def json_response():
    g.resp = JSONResponse()
    return None


@bp.route('/get_state', methods=['POST'])
@require_session
def get_state():
    g.resp.data['state'] = {}
    g.resp.data['error'] = []

    try:
        state = Controller().get_status()
    except ControllerError as e:
        err_msg = (
            'Exception getting current state from controller: {}'
            .format(str(e))
        )
        g.resp.data['error'].append(err_msg)
    else:
        # state = Heating / Cooling / Off
        nidoState = {'status': Status(state).name}
        g.resp.data['state'].update(nidoState)

    # Returns a JSON dict with an 'error' key on error
    # On success, returns a JSON dict with a 'conditions' key
    sensor_data = Sensor().get_conditions()
    if 'error' in sensor_data:
        g.resp.data['error'].append(sensor_data['error'])
    else:
        g.resp.data['state'].update(sensor_data)

    daemonState = {'daemon_running': Controller().daemon_running()}
    g.resp.data['state'].update(daemonState)

    if len(g.resp.data['error']) == 0:
        del g.resp.data['error']
    return g.resp.get_flask_response(current_app)


@bp.route('/get_weather', methods=['POST'])
@require_session
def get_weather():
    """
    Get local weather conditions via the Weather Underground API.
    Any errors will be passed through in the JSON response.
    The receiving application should note the retrieval_age value
    as necessary.
    TODO: Support caching built into the LocalWeather() object by
          storing the object in the session.
          Needs to be a serializable object (see Flask documentation).
    """
    g.resp.data = LocalWeather(
        current_app.config['WUNDERGROUND_API_KEY']
    ).get_conditions()
    return g.resp.get_flask_response(current_app)


@bp.route('/get_config', methods=['POST'])
@require_session
def get_config():
    cfg = Config().get_config()
    g.resp.data['config'] = cfg['config']
    return g.resp.get_flask_response(current_app)


@bp.route('/set_config', methods=['POST'])
@require_session
def set_config():
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
    if validate_json_req(new_cfg, validation):
        g.resp = set_config_helper(g.resp, cfg=new_cfg)
    else:
        g.resp.data['error'] = 'JSON in request was invalid.'
        g.resp.status = 400

    return g.resp.get_flask_response(current_app)
