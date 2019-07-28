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

from flask import Blueprint, current_app, request, g

from nido.web.api import require_secret, JSONResponse
from nido.lib.rpc.client import SchedulerClient
from nido.lib.exceptions import SchedulerClientError

bp = Blueprint("api_rpc", __name__)


@bp.before_app_request
def json_response():
    g.resp = JSONResponse()
    g.sc = SchedulerClient(
        current_app.config["RPC_HOST"], current_app.config["RPC_PORT"]
    )
    return None


@bp.route("/get/all", methods=["POST"])
@require_secret
def api_schedule_get_all():
    """Endpoint that returns all jobs in the scheduler."""
    g.sc.get_scheduled_jobs(g.resp.process_jobs)
    return g.resp.get_flask_response(current_app)


@bp.route("/get/<string:id>", methods=["POST"])
@require_secret
def api_schedule_get_jobid(id):
    """Endpoint that returns a scheduled job with a specific id."""
    try:
        g.sc.get_scheduled_job(g.resp.process_jobs, id)
    except SchedulerClientError as e:
        g.resp.data["error"] = "Error getting job: {}".format(e)
    return g.resp.get_flask_response(current_app)


@bp.route("/add/<string:type>", methods=["POST"])
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
    job_kwargs = request.get_json()
    del job_kwargs["secret"]

    if type.lower() == "mode" or type.lower() == "temp":
        try:
            g.sc.add_scheduled_job(g.resp.process_jobs, type, **job_kwargs)
        except SchedulerClientError as e:
            g.resp.data["error"] = "Error adding job: {}".format(e)
    else:
        g.resp.data["error"] = "Invalid mode specified."
        g.resp.status = 400

    return g.resp.get_flask_response(current_app)


@bp.route("/modify/<string:id>", methods=["POST"])
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
    job_kwargs = request.get_json()
    del job_kwargs["secret"]

    try:
        g.sc.modify_scheduled_job(g.resp.process_jobs, id, **job_kwargs)
    except SchedulerClientError as e:
        g.resp.data["error"] = "Error modifying job ID ({}): {}".format(id, e)

    return g.resp.get_flask_response(current_app)


@bp.route("/reschedule/<string:id>", methods=["POST"])
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
    job_kwargs = request.get_json()
    del job_kwargs["secret"]

    try:
        g.sc.reschedule_job(g.resp.process_jobs, id, **job_kwargs)
    except SchedulerClientError as e:
        g.resp.data["error"] = "Error rescheduling job ID ({}): {}".format(id, e)

    return g.resp.get_flask_response(current_app)


@bp.route("/pause/<string:id>", methods=["POST"])
@require_secret
def api_schedule_pause_jobid(id):
    try:
        g.sc.pause_scheduled_job(g.resp.process_jobs, id)
    except SchedulerClientError as e:
        g.resp.data["error"] = "Error pausing job: {}".format(e)

    return g.resp.get_flask_response(current_app)


@bp.route("/resume/<string:id>", methods=["POST"])
@require_secret
def api_schedule_resume_jobid(id):
    try:
        g.sc.resume_scheduled_job(g.resp.process_jobs, id)
    except SchedulerClientError as e:
        g.resp.data["error"] = "Error resuming job: {}".format(e)
    else:
        if g.resp.data == {}:
            g.resp.data["job"] = {"id": "{}".format(id)}
            g.resp.data[
                "message"
            ] = "The job would not have triggered again and has been deleted."

    return g.resp.get_flask_response(current_app)


@bp.route("/remove/<string:id>", methods=["POST"])
@require_secret
def api_schedule_remove_jobid(id):
    try:
        g.sc.remove_scheduled_job(id)
    except SchedulerClientError as e:
        g.resp.data["error"] = "Error removing job: {}".format(e)
    else:
        g.resp.data["job"] = {"id": "{}".format(id)}
        g.resp.data["message"] = "Job removed successfully."

    return g.resp.get_flask_response(current_app)
