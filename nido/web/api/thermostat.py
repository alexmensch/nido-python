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

from flask import Blueprint, current_app, g

from nido.lib import Mode, Status, c_to_f
from nido.web.api import require_secret, JSONResponse
from nido.lib.rpc.client import ThermostatClient
from nido.lib.exceptions import ThermostatClientError

bp = Blueprint("api_local", __name__)


@bp.before_app_request
def json_response():
    g.resp = JSONResponse()
    g.tc = ThermostatClient(
        current_app.config["RPC_HOST"], current_app.config["RPC_PORT"]
    )
    return None


@bp.route("/get/mode", methods=["POST"])
@require_secret
def api_get_mode():
    """Endpoint to get the current mode setting.

    The value returned is defined by the nido.lib.Mode Enum object.
    """
    try:
        mode = g.tc.get_mode()
    except ThermostatClientError as e:
        g.resp.data["error"] = "Error getting mode: {}".format(e)
        g.resp.status = 400
    else:
        g.resp.data["mode"] = {"value": mode, "name": Mode(mode).name}

    return g.resp.get_flask_response(current_app)


@bp.route("/set/mode/<string:mode>", methods=["POST"])
@require_secret
def api_set_mode(mode):
    """Endpoint to accept a new mode setting.

    Only setting one of the valid configured modes is possible.
    """
    try:
        g.tc.set_mode(mode)
    except ThermostatClientError as e:
        g.resp.data["error"] = "Error setting mode: {}".format(e)
        g.resp.status = 400
    else:
        g.resp.data["message"] = "Mode updated successfully."

    return g.resp.get_flask_response(current_app)


@bp.route("/get/temp/display_units", methods=["POST"])
@require_secret
def api_get_temp_units():
    celsius = g.tc.get_temp_units()
    if celsius:
        celsius = True
    else:
        celsius = False
    g.resp.data["celsius"] = celsius
    return g.resp.get_flask_response(current_app)


@bp.route('/set/temp/display_units/<regex("[cCfF]"):units>', methods=["POST"])
@require_secret
def api_set_temp_units(units):
    if units.upper() == "C":
        units = True
    else:
        units = False

    try:
        g.tc.set_temp_units(units)
    except ThermostatClientError as e:
        g.resp.data["error"] = "Error setting temperature display unit: {}".format(e)
        g.resp.status = 400
    else:
        g.resp.data["message"] = "Temperature display units updated successfully."

    return g.resp.get_flask_response(current_app)


@bp.route("/get/temp/target", methods=["POST"])
@require_secret
def api_get_set_temp():
    """Endpoint to get the current temperature. Always returned in Celsius."""
    try:
        temp_c = g.tc.get_set_temp()
    except ThermostatClientError as e:
        g.resp.data["error"] = "Error getting temperature from sensor: {}".format(e)
        g.resp.status = 400
    else:
        g.resp.data["temp"] = {"celsius": temp_c, "fahrenheit": c_to_f(temp_c)}

    return g.resp.get_flask_response(current_app)


@bp.route(
    '/set/temp/target/<regex("(([0-9]*)(\.([0-9]+))?)"):temp>/<regex("[cCfF]"):scale>',
    methods=["POST"],
)
@require_secret
def api_set_set_temp(temp, scale):
    """Endpoint to accept a new set temperature in either
    Celsius or Fahrenheit.

    The first regex accepts either integer or floating point numbers.
    """
    temp = float("{:.1f}".format(float(temp)))
    try:
        g.tc.set_temp(temp, scale)
    except ThermostatClientError as e:
        g.resp.data["error"] = "Error setting temperature: {}".format(e)
        g.resp.status = 400
    else:
        g.resp.data["message"] = "Temperature updated successfully."

    return g.resp.get_flask_response(current_app)


@bp.route("/get/conditions", methods=["POST"])
@require_secret
def api_get_conditions():
    try:
        g.resp.data = g.tc.get_conditions()
    except ThermostatClientError as e:
        g.resp.data["error"] = "Error getting sensor data: {}".format(e)
        g.resp.status = 400

    return g.resp.get_flask_response(current_app)


@bp.route("/get/state", methods=["POST"])
@require_secret
def api_get_state():
    try:
        state = g.tc.get_state()
    except ThermostatClientError as e:
        g.resp.data["error"] = "Error getting controller state: {}".format(e)
        g.resp.status = 400
    else:
        g.resp.data["state"] = {"value": state, "name": Status(state).name}

    return g.resp.get_flask_response(current_app)
