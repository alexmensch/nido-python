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

from past.builtins import basestring

from numbers import Number
from flask import Blueprint, current_app, g, request

from nido.auth import require_session
from nido.web import LocalWeather, validate_json_req
from nido.api import JSONResponse
from libnido.rpc.client import ThermostatClient
from libnido.exceptions import ThermostatClientError

bp = Blueprint("web_api", __name__)


@bp.before_app_request
def json_response():
    g.resp = JSONResponse()
    g.tc = ThermostatClient(
        current_app.config["RPC_HOST"], current_app.config["RPC_PORT"], json=True
    )
    return None


@bp.route("/get_state", methods=["POST"])
@require_session
def get_state():
    try:
        g.resp.data = g.tc.get_state()
    except ThermostatClientError as e:
        g.resp.data["error"] = "Error getting thermostat state: {}".format(e)
        g.resp.status = 400
    finally:
        return g.resp.get_flask_response(current_app)


@bp.route("/get_weather", methods=["POST"])
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
        current_app.config["WUNDERGROUND_API_KEY"]
    ).get_conditions()
    return g.resp.get_flask_response(current_app)


@bp.route("/get_config", methods=["POST"])
@require_session
def get_config():
    try:
        g.resp.data["config"] = g.tc.get_settings()
    except ThermostatClientError as e:
        g.resp.data["error"] = "Error getting configuration: {}".format(e)
        g.resp.status = 400
    finally:
        return g.resp.get_flask_response(current_app)


@bp.route("/set_config", methods=["POST"])
@require_session
def set_config():
    new_settings = request.get_json()

    # Expect to receive a json dict with
    # one or more of the following pairs
    validation = {"set_temp": Number, "set_mode": basestring, "celsius": bool}

    if validate_json_req(new_settings, validation):
        try:
            g.resp.data["config"] = g.tc.set_settings(**new_settings)
        except ThermostatClientError as e:
            g.resp.data["error"] = "Error updating configuration: {}".format(e)
            g.resp.status = 400
        else:
            g.resp.data["message"] = "Configuration updated successfully."
    else:
        g.resp.data["error"] = "JSON in request was invalid."
        g.resp.status = 400

    return g.resp.get_flask_response(current_app)
