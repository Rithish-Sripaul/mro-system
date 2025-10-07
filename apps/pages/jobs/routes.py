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
    general_schedule_jobs_list = list(
        jobs_collection.find({"schedule_type": "general_schedule"}).sort(
            "schedule_position", 1
        )
    )
    priority_schedule_jobs_list = list(
        jobs_collection.find({"schedule_type": "priority_schedule"}).sort(
            "schedule_position", 1
        )
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
        schedule_position = int(request.form.get("schedule_position"))

        # DOCUMENTS
        # File uploads will be handled by Dropzone.js and a separate endpoint

        date_format = "%m/%d/%Y %I:%M %p"
        completion_time = datetime.datetime.strptime(completion_time, date_format)

        # Incrementing positions of existing jobs if necessary
        if schedule_type in ["general_schedule", "priority_schedule"]:
            jobs_to_update = jobs_collection.find(
                {
                    "schedule_type": schedule_type,
                    "schedule_position": {"$gte": schedule_position},
                }
            )
            for job in jobs_to_update:
                new_position = job["schedule_position"] + 1
                jobs_collection.update_one(
                    {"_id": job["_id"]}, {"$set": {"schedule_position": new_position}}
                )

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
            "status": "pending",
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
        general_schedule_jobs_list=general_schedule_jobs_list,
        priority_schedule_jobs_list=priority_schedule_jobs_list,
    )
