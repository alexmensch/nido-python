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

from flask import current_app, g
from nido.api import bp, require_secret
from nido.lib.nidoserver import set_config_helper


@bp.route('/set/mode/<string:set_mode>', methods=['POST'])
@require_secret
def api_set_mode(set_mode):
    """Endpoint to accept a new mode setting.

    Only setting one of the valid configured modes is possible.
    """
    g.resp = set_config_helper(g.resp, mode=set_mode)
    return g.resp.get_flask_response(current_app)


@bp.route(
    '/set/temp/<regex("(([0-9]*)(\.([0-9]+))?)"):temp>'
    '/<regex("[cCfF]"):scale>', methods=['POST']
)
@require_secret
def api_set_temp(temp, scale):
    """Endpoint to accept a new set temperature in either
    Celsius or Fahrenheit.

    The first regex accepts either integer or floating point numbers.
    """
    temp = float("{:.1f}".format(float(temp)))
    g.resp = set_config_helper(g.resp, temp_scale=[temp, scale])
    return g.resp.get_flask_response(current_app)
