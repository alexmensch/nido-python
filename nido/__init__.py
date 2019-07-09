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

from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from future import standard_library
standard_library.install_aliases()
from builtins import *

import os
import logging
from flask import Flask, render_template

handler = logging.StreamHandler()
formatter = logging.Formatter(
    fmt='%(asctime)s [%(levelname)s] %(name)s | %(message)s',
    datefmt='%d/%m/%Y %H:%M:%S'
)
handler.setFormatter(formatter)
root = logging.getLogger()
if 'NIDO_DEBUG' in os.environ:
    root.setLevel(logging.DEBUG)
else:
    root.setLevel(logging.INFO)
root.addHandler(handler)


def create_app(test_config=None):
    app = Flask('nido', instance_path='instance',
                instance_relative_config=True)

    if test_config is None:
        if 'NIDO_DEBUG' in os.environ:
            config_object = 'nido.config.DevelopmentConfig'
        else:
            config_object = 'nido.config.ProductionConfig'
        app.config.from_object(config_object)
    else:
        app.config.from_mapping(test_config)
    # Load private config values from instance folder
    app.config.from_pyfile('private-config.py')

    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    @app.route('/')
    def render_ui():
        """The / route only serves to return the React-based UI."""
        return render_template(
            'index.html',
            google_api_key=app.config['GOOGLE_API_KEY']
        )

    from nido import auth
    from nido.web import web_api
    from nido.api import thermostat, schedule, RegexConverter
    app.url_map.converters['regex'] = RegexConverter
    app.register_blueprint(auth.bp)
    app.register_blueprint(web_api.bp)
    app.register_blueprint(thermostat.bp, url_prefix='/api')
    app.register_blueprint(schedule.bp, url_prefix='/api/schedule')

    return app
