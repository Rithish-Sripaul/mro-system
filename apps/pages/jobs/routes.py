import os
import click
import datetime
import json
from pymongo import MongoClient
from flask import Blueprint, current_app, flash, g
from functools import wraps
from flask import session, redirect, url_for, render_template, request
from apps.pages.database import get_db


blueprint = Blueprint("jobs", __name__, url_prefix="/jobs")


@blueprint.route("/manage_jobs", methods=["GET", "POST"])
def manage_jobs():
    db = get_db()
    users_collection = db["users"]
    divisions_collection = db["divisions"]
    jobs_collection = db["jobs"]

    user_list = list(users_collection.find({}, {"_id": 1, "name": 1}).sort("name", 1))
    divisions_list = list(
        divisions_collection.find({}, {"_id": 1, "name": 1}).sort("name", 1)
    )

    if request.method == "POST":
        # Handle form submission

        # BASIC JOB DETAILS
        job_name = request.form.get("job_name")
        divisions = request.form.getlist("divisions")
        coordinators = request.form.getlist("coordinators")
        description = request.form.get("description")
        tags_json_string = request.form.get("tags")

        # DEADLINES AND SCHEDULING
        start_time = datetime.datetime.now()
        completion_time = request.form.get("completion_time")
        schedule_type = request.form.get("schedule_type")
        schedule_position = request.form.get("schedule_position")

        # DOCUMENTS
        # File uploads will be handled by Dropzone.js and a separate endpoint

        date_format = "%m/%d/%Y %I:%M %p"
        completion_time = datetime.datetime.strptime(completion_time, date_format)

        tags = []
        if tags_json_string:
            try:
                tags_data = json.loads(tags_json_string)
                tags = [tag["value"] for tag in tags_data if "value" in tag]
            except json.JSONDecodeError:
                tags = []

        # Insert into MongoDB
        job_data = {
            "job_name": job_name,
            "divisions": divisions,
            "coordinators": coordinators,
            "description": description,
            "tags": tags,
            "start_time": start_time,
            "completion_time": completion_time,
            "schedule_type": schedule_type,
            "schedule_position": schedule_position,
            "created_at": datetime.datetime.now(),
            "updated_at": datetime.datetime.now(),
        }
        jobs_collection.insert_one(job_data)
        return redirect(url_for("jobs.manage_jobs"))

    return render_template(
        "pages/jobs/manage_jobs.html",
        divisions_list=divisions_list,
        user_list=user_list,
    )
