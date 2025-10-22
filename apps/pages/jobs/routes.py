import os
import click
import datetime
import json
from flask_login import current_user
from pymongo import MongoClient
from flask import Blueprint, Response, current_app, flash, g, jsonify
from functools import wraps
from flask import session, redirect, url_for, render_template, request
from apps.pages.authentication.routes import login_required
from apps.pages.database import get_db
from bson.objectid import ObjectId

blueprint = Blueprint("jobs", __name__, url_prefix="/jobs")


# View jobs
@blueprint.route("/view_jobs", methods=["GET"])
def view_jobs():
    db = get_db()
    jobs_collection = db["jobs"]

    jobs_list = list(jobs_collection.find({}).sort("created_at", -1))
    return render_template("pages/jobs/view-jobs.html", jobs=jobs_list)


# Manage Jobs
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

    jobs_list = list(jobs_collection.find({}).sort("created_at", -1))
    divisions_dict = {div["_id"]: div["name"] for div in divisions_list}
    print(divisions_dict)

    if request.method == "POST":
        # Handle form submission

        # BASIC JOB DETAILS
        job_name = request.form.get("job_name")
        job_color = request.form.get("job_color")
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
        divisions = list(map(lambda x: ObjectId(x), divisions))

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
            "job_color": job_color,
            "divisions": divisions,
            "coordinators": coordinators,
            "description": description,
            "tags": tags,
            "status": "pending",
            "start_time": start_time,
            "completion_time": completion_time,
            "schedule_type": schedule_type,
            "schedule_position": schedule_position,
            "document_ids": [],
            "created_at": datetime.datetime.now(),
            "updated_at": datetime.datetime.now(),
        }
        jobs_collection.insert_one(job_data)
        return redirect(url_for("jobs.manage_jobs"))

    return render_template(
        "pages/jobs/manage-jobs.html",
        divisions_list=divisions_list,
        user_list=user_list,
        general_schedule_jobs_list=general_schedule_jobs_list,
        priority_schedule_jobs_list=priority_schedule_jobs_list,
        jobs_list=jobs_list,
        divisions_dict=divisions_dict,
    )


# Job Details
@blueprint.route("/job_details/<job_id>", methods=["GET", "POST"])
def job_details(job_id):
    db = get_db()
    jobs_collection = db["jobs"]
    users_collection = db["users"]
    divisions_collection = db["divisions"]

    divisions_dict = {
        div["_id"]: div["name"]
        for div in divisions_collection.find({}, {"_id": 1, "name": 1})
    }

    job = jobs_collection.find_one({"_id": ObjectId(job_id)})

    return render_template(
        "pages/jobs/job-details.html", job=job, divisions_dict=divisions_dict
    )

from bson import json_util

@blueprint.route("/<string:job_id>/comments", methods=["GET"])
def get_comments(job_id):
    """
    Fetches all comments for a specific job, sorted by timestamp.
    """
    try:
        # FIX 1: Added get_db()
        db = get_db() 
        
        comments_cursor = db.comments.find(
            {"document_id": ObjectId(job_id), "context": "job"}
        ).sort(
            "timestamp", 1
        )  # Ascending order

        comments_list = list(comments_cursor)

        # FIX 2: Use json_util.dumps to handle ObjectId and datetime
        return Response(
            json_util.dumps(comments_list), 200, {"Content-Type": "application/json"}
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@blueprint.route("/<string:job_id>/comments", methods=["POST"])
@login_required  # Protect this route
def post_comment(job_id):
    """
    Posts a new comment or a reply.
    """
    try:
        db = get_db()
        comments_collection = db["comments"]
        data = request.get_json()
        text = data.get("text")
        parent_id = data.get("parent_id")  # This will be null for top-level comments

        if not text:
            return jsonify({"error": "Comment text is required"}), 400

        # FIX 3: Make avatar_url dynamic and add a default fallback
        # Use session.get() to avoid errors if the key doesn't exist
        user_avatar = "{{config.ASSETS_ROOT}}/images/users/user-10.jpg"

        new_comment = {
            "document_id": ObjectId(job_id),
            "context": "job",
            "user_id": ObjectId(session["user_id"]),
            "username": session["user_name"],
            "avatar_url": user_avatar, # Use the dynamic variable here
            "text": text,
            "timestamp": datetime.datetime.now(),
            "parent_id": ObjectId(parent_id) if parent_id else None,
        }

        result = comments_collection.insert_one(new_comment)
        created_comment = comments_collection.find_one({"_id": result.inserted_id})

        # FIX 2: Use json_util.dumps here as well
        return Response(
            json_util.dumps(created_comment),
            201,
            {"Content-Type": "application/json"},
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500