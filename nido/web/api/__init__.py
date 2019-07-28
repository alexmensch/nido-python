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
from flask import current_app, request
from werkzeug.routing import BaseConverter
import json

from nido.lib.exceptions import SchedulerClientError


def require_secret(route):
    """Decorator for API routes to verify that client supplied a secret
    in the request body.
    """

    @wraps(route)
    def check_secret(*args, **kwargs):
        req_data = request.get_json()
        # Prepare a JSONResponse in case we need it
        resp = JSONResponse()

        if "secret" in list(req_data.keys()):
            if req_data["secret"] == current_app.config["PUBLIC_API_SECRET"]:
                return route(*args, **kwargs)
            else:
                resp.data["error"] = "Invalid secret."
                resp.status = 401
        else:
            resp.data["error"] = "JSON in request was invalid."
            resp.status = 400

        return resp.get_flask_response(current_app)

    return check_secret


class JSONResponse(object):
    def __init__(self):
        self.status = 200
        self.data = {}
        return None

    def get_flask_response(self, app):
        response = app.make_response(
            json.dumps(self.data, sort_keys=True, ensure_ascii=False)
        )
        response.headers["Content-Type"] = "application/json"
        response.status_code = self.status
        return response

    def process_jobs(self, jobs):
        """This method is only passed as a callback reference to
        nido.lib.rpc.client.SchedulerClient.
        """
        if isinstance(jobs, list):
            job_list = []
            for j in jobs:
                if j is None:
                    continue
                job_list.append(self._jsonify_job(j))
            self.data["jobs"] = job_list
        else:
            self.data["job"] = self._jsonify_job(jobs)
        return None

    def _jsonify_job(self, j):
        """Converts apscheduler.job.Job object to a JSON representation.

        The 'trigger' representation varies depending on the trigger object that was
        assigned to the job. Should be one of:
            apscheduler.triggers.cron.CronTrigger
            apscheduler.triggers.date.DateTrigger
            apscheduler.triggers.interval.IntervalTrigger

        The 'misfire_grace_time' key represents the time in seconds of how long the
        job's execution is allowed to be late.

        Full API documentation is available here:
        https://apscheduler.readthedocs.io/en/v3.6.0/py-modindex.html
        """
        if j is None:
            raise SchedulerClientError("No job exists with that ID.")

        try:
            # Test if j.trigger is a DateTrigger type
            trigger = {"timezone": str(j.trigger.run_date.tzinfo)}
        except AttributeError:
            trigger_start_date = (
                j.trigger.start_date.strftime("%m/%d/%Y %H:%M:%S")
                if j.trigger.start_date
                else None
            )
            trigger_end_date = (
                j.trigger.end_date.strftime("%m/%d/%Y %H:%M:%S")
                if j.trigger.end_date
                else None
            )
            trigger = {
                "start_date": trigger_start_date,
                "end_date": trigger_end_date,
                "timezone": str(j.trigger.timezone),
            }

        try:
            # Test if j.trigger is a CronTrigger type
            j.trigger.fields
        except AttributeError:
            try:
                # Test if j.trigger is an IntervalTrigger type
                trigger_interval = (
                    str(j.trigger.interval) if j.trigger.interval else None
                )
            except AttributeError:
                try:
                    trigger["run_date"] = j.trigger.run_date.strftime(
                        "%m/%d/%Y %H:%M:%S"
                    )
                except AttributeError:
                    raise SchedulerClientError(
                        "Unknown trigger type: {}".format(type(j.trigger))
                    )
            else:
                trigger["interval"] = trigger_interval
        else:
            trigger["cron"] = {}
            for f in j.trigger.fields:
                trigger["cron"][f.name] = str(f)

        job = {
            "id": str(j.id),
            "name": str(j.name),
            "misfire_grace_time": str(j.misfire_grace_time),
            "next_run_time": (
                j.next_run_time.strftime("%m/%d/%Y %H:%M:%S")
                if j.next_run_time
                else None
            ),
            "trigger": trigger,
        }

        return job


class RegexConverter(BaseConverter):
    """Custom URL converter to allow use of regular expressions.
    Source: https://stackoverflow.com/questions/5870188\
    /does-flask-support-regular-expressions-in-its-url-routing
    """

    def __init__(self, url_map, *items):
        super(RegexConverter, self).__init__(url_map)
        self.regex = items[0]
