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

from copy import copy
from functools import wraps
from flask import current_app, request
from werkzeug.routing import BaseConverter
import json

from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.date import DateTrigger

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
        self.data["jobs"] = self._jsonify_jobs(jobs)
        return None

    def _jsonify_jobs(self, jobs):
        job_list = []
        for j in jobs:
            if j is None:
                continue
            job_list.append(self._jsonify_job(j))
        return job_list

    def _jsonify_job(self, j):
        if j is None:
            raise SchedulerClientError("No job exists with that ID.")
        if isinstance(j.trigger, DateTrigger):
            trigger = {"timezone": str(j.trigger.run_date.tzinfo)}
        else:
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

        if isinstance(j.trigger, CronTrigger):
            trigger["cron"] = {}
            for f in j.trigger.fields:
                trigger["cron"][f.name] = str(f)
        elif isinstance(j.trigger, IntervalTrigger):
            trigger_interval = str(j.trigger.interval) if j.trigger.interval else None
            trigger["interval"] = trigger_interval
        elif isinstance(j.trigger, DateTrigger):
            trigger["run_date"] = j.trigger.run_date.strftime("%m/%d/%Y %H:%M:%S")
        else:
            raise SchedulerClientError(
                "Unknown trigger type: {}".format(type(j.trigger))
            )

        job = {
            "id": copy(j.id),
            "name": copy(j.name),
            "args": copy(str(j.args)),
            "next_run_time": (
                copy(j.next_run_time).strftime("%m/%d/%Y %H:%M:%S")
                if j.next_run_time
                else None
            ),
            "trigger": trigger,
        }

        return job


# Custom URL converter to allow use of regex
# Source: https://stackoverflow.com/questions/5870188 \
# /does-flask-support-regular-expressions-in-its-url-routing
#
class RegexConverter(BaseConverter):
    """Custom URL converter to allow use of regular expressions.
    Source: https://stackoverflow.com/questions/5870188\
    /does-flask-support-regular-expressions-in-its-url-routing
    """

    def __init__(self, url_map, *items):
        super(RegexConverter, self).__init__(url_map)
        self.regex = items[0]
