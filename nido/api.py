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
from flask import Blueprint, current_app, request, g
from .lib.nidoserver import JSONResponse, set_config_helper
from .lib.scheduler import NidoDaemonService, NidoDaemonServiceError

bp = Blueprint('api', __name__, url_prefix='/api')


def require_secret(route):
    """Decorator for API routes to verify that client supplied a secret
    in the request body.
    """
    @wraps(route)
    def check_secret(*args, **kwargs):
        req_data = request.get_json()
        # Prepare a JSONResponse in case we need it
        resp = JSONResponse()

        if 'secret' in list(req_data.keys()):
            if req_data['secret'] == current_app.config['PUBLIC_API_SECRET']:
                return route(*args, **kwargs)
            else:
                resp.data['error'] = 'Invalid secret.'
                resp.status = 401
        else:
            resp.data['error'] = 'JSON in request was invalid.'
            resp.status = 400

        return resp.get_flask_response()

    return check_secret


@bp.before_app_request
def json_response():
    g.resp = JSONResponse()
    return None


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


@bp.route('/schedule/get/all', methods=['POST'])
@require_secret
def api_schedule_get_all():
    """Endpoint that returns all jobs in the scheduler."""
    nds = NidoDaemonService(json=True)
    g.resp.data['jobs'] = nds.get_scheduled_jobs()
    return g.resp.get_flask_response(current_app)


@bp.route('/schedule/get/<string:id>', methods=['POST'])
@require_secret
def api_schedule_get_jobid(id):
    """Endpoint that returns a scheduled job with a specific id."""
    nds = NidoDaemonService(json=True)
    try:
        g.resp.data['job'] = nds.get_scheduled_job(id)
    except NidoDaemonServiceError as e:
        g.resp.data['error'] = 'Error getting job: {}'.format(e)
    return g.resp.get_flask_response(current_app)


@bp.route('/schedule/add/<string:type>', methods=['POST'])
@require_secret
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


@bp.route('/schedule/modify/<string:id>', methods=['POST'])
@require_secret
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


@bp.route('/schedule/reschedule/<string:id>', methods=['POST'])
@require_secret
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


@bp.route('/schedule/pause/<string:id>', methods=['POST'])
@require_secret
def api_schedule_pause_jobid(id):
    resp = ns.JSONResponse()
    nds = NidoDaemonService(json=True)
    try:
        resp.data['job'] = nds.pause_scheduled_job(id)
    except NidoDaemonServiceError as e:
        resp.data['error'] = 'Error pausing job: {}'.format(e)
    return resp.get_flask_response(app)


@bp.route('/schedule/resume/<string:id>', methods=['POST'])
@require_secret
def api_schedule_resume_jobid(id):
    resp = ns.JSONResponse()
    nds = NidoDaemonService(json=True)
    try:
        resp.data['job'] = nds.resume_scheduled_job(id)
    except NidoDaemonServiceError as e:
        resp.data['error'] = 'Error resuming job: {}'.format(e)
    return resp.get_flask_response(app)


@bp.route('/schedule/remove/<string:id>', methods=['POST'])
@require_secret
def api_schedule_remove_jobid(id):
    resp = ns.JSONResponse()
    nds = NidoDaemonService(json=True)
    try:
        resp.data['job'] = nds.remove_scheduled_job(id)
    except NidoDaemonServiceError as e:
        resp.data['error'] = 'Error removing job: {}'.format(e)
    return resp.get_flask_response(app)
