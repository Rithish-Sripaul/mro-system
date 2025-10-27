import os
import click
import datetime
import json
import math
from flask_login import current_user
from pymongo import MongoClient
from flask import Blueprint, Response, current_app, flash, g, jsonify
from functools import wraps
from flask import session, redirect, url_for, render_template, request
from apps.pages.authentication.routes import login_required
from apps.pages.database import get_db
from bson.objectid import ObjectId
from werkzeug.utils import secure_filename
from gridfs import GridFS
from io import BytesIO

blueprint = Blueprint("jobs", __name__, url_prefix="/jobs")


# View jobs
@blueprint.route("/view_jobs", methods=["GET"])
def view_jobs():
    db = get_db()
    users_collection = db["users"]

    # --- Get filter values from request ---
    search_query = request.args.get("q", "").strip()
    status_filter = request.args.get("status", "")
    team_filter = request.args.get("team", "")
    deadline_filter = request.args.get("deadline", "")

    # --- Build the match pipeline for filtering ---
    match_pipeline = {}
    if search_query:
        match_pipeline["job_name"] = {"$regex": search_query, "$options": "i"}
    if status_filter:
        match_pipeline["status"] = status_filter
    if team_filter:
        match_pipeline["coordinators"] = (
            team_filter  # Assumes coordinator IDs are stored as strings
        )

    if deadline_filter:
        now = datetime.datetime.now()
        today = now.replace(hour=0, minute=0, second=0, microsecond=0)
        if deadline_filter == "today":
            tomorrow = today + datetime.timedelta(days=1)
            match_pipeline["completion_time"] = {"$gte": today, "$lt": tomorrow}
        elif deadline_filter == "this_week":
            start_of_week = today - datetime.timedelta(days=today.weekday())
            end_of_week = start_of_week + datetime.timedelta(days=7)
            match_pipeline["completion_time"] = {
                "$gte": start_of_week,
                "$lt": end_of_week,
            }
        elif deadline_filter == "this_month":
            next_month = today.replace(day=28) + datetime.timedelta(days=4)
            start_of_month = next_month.replace(day=1)
            end_of_month = (
                start_of_month.replace(day=28) + datetime.timedelta(days=4)
            ).replace(day=1)
            match_pipeline["completion_time"] = {
                "$gte": start_of_month,
                "$lt": end_of_month,
            }

    # --- Pagination Logic ---
    page = request.args.get("page", 1, type=int)
    per_page = 8  # Number of jobs per page
    skip = (page - 1) * per_page

    # --- Create a base pipeline and one for counting ---
    base_pipeline = []
    if match_pipeline:
        base_pipeline.append({"$match": match_pipeline})

    # Get total count of filtered documents
    count_pipeline = base_pipeline + [{"$count": "total"}]
    count_result = list(db.jobs.aggregate(count_pipeline))
    total_jobs = count_result[0]["total"] if count_result else 0
    total_pages = math.ceil(total_jobs / per_page)

    # --- Main data fetching pipeline ---
    pipeline = base_pipeline + [
        # Sort jobs by creation date
        {"$sort": {"created_at": -1}},
        {"$skip": skip},
        {"$limit": per_page},
        # Lookup for comments count
        {
            "$lookup": {
                "from": "comments",
                "localField": "_id",
                "foreignField": "document_id",
                "as": "comments_info",
            }
        },
        # Lookup for files count
        {
            "$lookup": {
                "from": "job_files_metadata",
                "localField": "_id",
                "foreignField": "job_id",
                "as": "files_info",
            }
        },
        # Convert coordinator string IDs to ObjectIds for the next lookup
        {
            "$addFields": {
                "coordinator_oids": {
                    "$map": {
                        "input": "$coordinators",
                        "as": "coordId",
                        "in": {"$toObjectId": "$$coordId"},
                    }
                }
            }
        },
        # Lookup for coordinator details
        {
            "$lookup": {
                "from": "users",
                "localField": "coordinator_oids",
                "foreignField": "_id",
                "as": "coordinator_details",
            }
        },
        # Lookup for division details
        {
            "$lookup": {
                "from": "divisions",
                "localField": "divisions",  # This should be an array of ObjectIds
                "foreignField": "_id",
                "as": "division_details",
            }
        },
        # Add counts and coordinator details to the main document
        {
            "$addFields": {
                "comments_count": {"$size": "$comments_info"},
                "files_count": {"$size": "$files_info"},
                "coordinators_list": "$coordinator_details",
                "divisions_list": "$division_details",
            }
        },
    ]

    jobs_list = list(db.jobs.aggregate(pipeline)) if total_jobs > 0 else []

    # --- Data for filter dropdowns ---
    all_teams = list(
        users_collection.find({}, {"_id": 1, "name": 1, "avatar_url": 1}).sort(
            "name", 1
        )
    )
    all_statuses = [
        {"value": "pending", "text": "Pending"},
        {"value": "in_progress", "text": "In Progress"},
        {"value": "completed", "text": "Completed"},
        {"value": "on_hold", "text": "On Hold"},
    ]

    return render_template(
        "pages/jobs/view-jobs.html",
        jobs=jobs_list,
        page=page,
        total_pages=total_pages,
        total_jobs=total_jobs,
        all_teams=all_teams,
        all_statuses=all_statuses,
        filters={
            "q": search_query,
            "status": status_filter,
            "team": team_filter,
            "deadline": deadline_filter,
        },
    )


# View jobs list
@blueprint.route("/view_jobs_list", methods=["GET"])
def view_jobs_list():
    db = get_db()
    users_collection = db["users"]
    divisions_collection = db["divisions"]

    # --- Get filter values from request (for passing back to view-jobs link) ---
    search_query = request.args.get("q", "")
    status_filter = request.args.get("status", "")
    team_filter = request.args.get("team", "")
    deadline_filter = request.args.get("deadline", "")

    # --- Aggregation for Widgets ---
    widget_pipeline = [
        {
            "$group": {
                "_id": None,
                "total_jobs": {"$sum": 1},
                "pending_jobs": {
                    "$sum": {"$cond": [{"$eq": ["$status", "pending"]}, 1, 0]}
                },
                "in_progress_jobs": {
                    "$sum": {"$cond": [{"$eq": ["$status", "in_progress"]}, 1, 0]}
                },
                "completed_jobs": {
                    "$sum": {"$cond": [{"$eq": ["$status", "completed"]}, 1, 0]}
                },
            }
        }
    ]
    widget_data = list(db.jobs.aggregate(widget_pipeline))
    widgets = (
        widget_data[0]
        if widget_data
        else {
            "total_jobs": 0,
            "pending_jobs": 0,
            "in_progress_jobs": 0,
            "completed_jobs": 0,
        }
    )

    # --- Main data fetching pipeline ---
    pipeline = [
        {"$sort": {"created_at": -1}},
        # Lookup for division details
        {
            "$lookup": {
                "from": "divisions",
                "localField": "divisions",  # This should be an array of ObjectIds
                "foreignField": "_id",
                "as": "division_details",
            }
        },
        # Add division details to the main document
        {
            "$addFields": {
                "divisions_list": "$division_details",
            }
        },
    ]
    jobs_list = list(db.jobs.aggregate(pipeline)) if widgets["total_jobs"] > 0 else []

    # --- Data for divisions dictionary ---
    divisions_dict = {
        div["_id"]: div["name"]
        for div in divisions_collection.find({}, {"_id": 1, "name": 1})
    }

    # --- Data for filter dropdowns ---
    all_teams = list(
        users_collection.find({}, {"_id": 1, "name": 1, "avatar_url": 1}).sort(
            "name", 1
        )
    )
    all_statuses = [
        {"value": "pending", "text": "Pending"},
        {"value": "in_progress", "text": "In Progress"},
        {"value": "completed", "text": "Completed"},
        {"value": "on_hold", "text": "On Hold"},
    ]

    return render_template(
        "pages/jobs/view-jobs-list.html",
        jobs_list=jobs_list,
        all_teams=all_teams,
        all_statuses=all_statuses,
        divisions_dict=divisions_dict,
        widgets=widgets,
        filters={
            "q": search_query,
            "status": status_filter,
            "team": team_filter,
            "deadline": deadline_filter,
        },
    )


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


def build_comment_tree(comments):
    """
    Helper function to build a nested tree from a flat list of comments.
    """
    comment_map = {}
    tree = []

    # Create a map of all comments by their ID
    for comment in comments:
        comment_id_str = str(comment["_id"])
        comment_map[comment_id_str] = {**comment, "replies": []}

    # Build the tree structure
    for comment_id, comment in comment_map.items():
        parent_id = comment.get("parent_id")
        parent_id_str = str(parent_id) if parent_id else None

        if parent_id_str and parent_id_str in comment_map:
            # It's a reply, add it to its parent's replies array
            comment_map[parent_id_str]["replies"].append(comment)
        else:
            # It's a top-level comment
            tree.append(comment)

    return tree


@blueprint.route("/<string:job_id>/comments", methods=["GET"])
def get_comments(job_id):
    """
    Fetches comments for a specific job, with pagination for top-level comments.
    """
    try:
        db = get_db()

        # 1. Get page number from query args, default to 1
        page = request.args.get("page", 1, type=int)
        limit = 5  # Show 5 top-level comments per page
        skip = (page - 1) * limit

        # 2. Fetch *all* comments for this job (we need them all to build the tree)
        all_comments_cursor = db.comments.find(
            {"document_id": ObjectId(job_id), "context": "job"}
        ).sort(
            "timestamp", 1
        )  # Sort oldest to newest to build tree correctly

        all_comments = list(all_comments_cursor)

        # 3. Build the *full* nested tree
        comment_tree = build_comment_tree(all_comments)

        # 4. Sort the *top-level* comments (newest first)
        comment_tree.sort(key=lambda x: x["timestamp"], reverse=True)

        # 5. Get pagination info
        total_top_level_comments = len(comment_tree)
        total_pages = math.ceil(total_top_level_comments / limit)
        has_more = page < total_pages

        # 6. Get the *slice* for the current page
        paginated_tree_slice = comment_tree[skip : skip + limit]

        # 7. Prepare the response
        response_data = {
            "comments": paginated_tree_slice,  # This list contains nested replies
            "pagination": {
                "page": page,
                "limit": limit,
                "total_pages": total_pages,
                "total_comments": len(
                    all_comments
                ),  # Total of all comments (incl. replies)
                "has_more": has_more,
            },
        }

        return Response(
            json_util.dumps(response_data), 200, {"Content-Type": "application/json"}
        )

    except Exception as e:
        print(f"Error in get_comments: {e}")
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

        # --- FIX: Use the avatar_url from the session ---
        user_avatar = session.get(
            "avatar_url", "{{config.ASSETS_ROOT}}/images/users/user-placeholder.jpg"
        )
        # --- END FIX ---

        new_comment = {
            "document_id": ObjectId(job_id),
            "context": "job",
            "user_id": ObjectId(session["user_id"]),
            "username": session["user_name"],
            "avatar_url": user_avatar,  # Use the dynamic variable here
            "text": text,
            "timestamp": datetime.datetime.now(),
            "parent_id": ObjectId(parent_id) if parent_id else None,
        }

        result = comments_collection.insert_one(new_comment)
        created_comment = comments_collection.find_one({"_id": result.inserted_id})

        return Response(
            json_util.dumps(created_comment),
            201,
            {"Content-Type": "application/json"},
        )

    except Exception as e:
        print(f"Error in post_comment: {e}")
        return jsonify({"error": str(e)}), 500


@blueprint.route("/<string:job_id>/team", methods=["GET"])
def get_job_team(job_id):
    """
    Fetches the details of team members (coordinators) assigned to a job.
    """
    try:
        db = get_db()
        jobs_collection = db["jobs"]
        users_collection = db["users"]

        job = jobs_collection.find_one({"_id": ObjectId(job_id)}, {"coordinators": 1})

        if not job:
            return jsonify({"error": "Job not found"}), 404

        coordinator_ids_str = job.get("coordinators", [])
        if not coordinator_ids_str:
            return jsonify([])  # Return empty list if no coordinators

        # Convert string IDs back to ObjectIds for querying
        coordinator_object_ids = [ObjectId(uid) for uid in coordinator_ids_str]

        # Fetch user details for the coordinators
        # Select only necessary fields: _id, name, avatar_url, and maybe role/title
        team_members_cursor = users_collection.find(
            {"_id": {"$in": coordinator_object_ids}},
            {
                "_id": 1,
                "name": 1,
                "avatar_url": 1,
                "role": 1,
            },  # Assuming users have a 'role' field
        )

        team_members = list(team_members_cursor)

        # Use json_util.dumps to handle ObjectIds correctly
        return Response(
            json_util.dumps(team_members), 200, {"Content-Type": "application/json"}
        )

    except Exception as e:
        print(f"Error in get_job_team: {e}")
        return jsonify({"error": str(e)}), 500


@blueprint.route("/<string:job_id>/files", methods=["POST"])
@login_required
def upload_job_file(job_id):
    """Handles file uploads for a specific job using GridFS."""
    db = get_db()
    # --- Initialize GridFS ---
    fs = GridFS(db)
    files_metadata_collection = db["job_files_metadata"]  # Collection for metadata
    jobs_collection = db["jobs"]

    # Check if the job exists
    job = jobs_collection.find_one({"_id": ObjectId(job_id)})
    if not job:
        return jsonify({"error": "Job not found"}), 404

    if "file" not in request.files:
        return jsonify({"error": "No file part in the request"}), 400

    file = request.files["file"]

    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    if file:
        original_filename = secure_filename(file.filename)
        content_type = file.content_type

        try:
            # --- Save file to GridFS ---
            # fs.put() stores the file and returns its _id
            gridfs_file_id = fs.put(
                file,  # The file stream
                filename=original_filename,  # Store original name in GridFS too
                content_type=content_type,
                job_id=ObjectId(job_id),  # Add custom metadata
                uploader_user_id=ObjectId(session["user_id"]),
            )

            # --- Retrieve GridFS file info to get size ---
            gridfs_file_info = fs.get(gridfs_file_id)

            # --- Save METADATA to a separate collection ---
            file_metadata = {
                "job_id": ObjectId(job_id),
                "operation_id": None,
                "gridfs_id": gridfs_file_id,  # Link to the file in GridFS
                "original_filename": original_filename,
                "content_type": content_type,
                "size": gridfs_file_info.length,  # Get size from GridFS file info
                "upload_timestamp": gridfs_file_info.upload_date,  # Use GridFS timestamp
                "uploader_user_id": ObjectId(session["user_id"]),
                "uploader_username": session["user_name"],
            }

            result = files_metadata_collection.insert_one(file_metadata)
            inserted_metadata = files_metadata_collection.find_one(
                {"_id": result.inserted_id}
            )

            return Response(
                json_util.dumps(inserted_metadata),
                201,
                {"Content-Type": "application/json"},
            )

        except Exception as e:
            print(f"Error uploading file to GridFS: {e}")
            # GridFS errors might not leave partial files, but good to log
            return jsonify({"error": f"Could not save file to GridFS: {e}"}), 500

    return jsonify({"error": "Unknown error occurred"}), 500


@blueprint.route("/<string:job_id>/files", methods=["GET"])
@login_required
def get_job_files(job_id):
    """Lists file metadata associated with a job."""
    try:
        db = get_db()
        # --- Query the metadata collection ---
        files_metadata_collection = db["job_files_metadata"]

        job_files_cursor = files_metadata_collection.find(
            {"job_id": ObjectId(job_id)}
        ).sort(
            "upload_timestamp", -1
        )  # Show newest first

        job_files_metadata = list(job_files_cursor)

        return Response(
            json_util.dumps(job_files_metadata),
            200,
            {"Content-Type": "application/json"},
        )
    except Exception as e:
        print(f"Error getting job file metadata: {e}")
        return jsonify({"error": str(e)}), 500


@blueprint.route("/files/<string:metadata_id>/download", methods=["GET"])
@login_required
def download_job_file(metadata_id):
    """Allows downloading a specific file from GridFS."""
    try:
        db = get_db()
        fs = GridFS(db)
        files_metadata_collection = db["job_files_metadata"]

        # --- Find the METADATA document first ---
        file_metadata = files_metadata_collection.find_one(
            {"_id": ObjectId(metadata_id)}
        )

        if not file_metadata:
            return jsonify({"error": "File metadata not found"}), 404

        gridfs_id = file_metadata.get("gridfs_id")
        if not gridfs_id:
            return jsonify({"error": "GridFS ID missing in metadata"}), 500

        # --- Get the file from GridFS using the ID from metadata ---
        gridfs_file = fs.get(gridfs_id)

        # --- Create a Flask Response to stream the file ---
        response = Response(gridfs_file, mimetype=gridfs_file.content_type)
        # Set headers for download
        response.headers["Content-Length"] = gridfs_file.length
        response.headers["Content-Disposition"] = (
            f'attachment; filename="{gridfs_file.filename}"'  # Use filename stored in GridFS
        )

        return response

    except Exception as e:
        print(f"Error downloading file from GridFS: {e}")
        return jsonify({"error": str(e)}), 500


# Optional: Add DELETE route - needs to delete from GridFS and metadata collection
@blueprint.route("/files/<string:metadata_id>", methods=["DELETE"])
@login_required
def delete_job_file(metadata_id):
    """Deletes a file from GridFS and its associated metadata."""
    db = get_db()
    fs = GridFS(db)
    files_metadata_collection = db["job_files_metadata"]

    try:
        # --- Find and delete the METADATA document first ---
        metadata = files_metadata_collection.find_one_and_delete(
            {"_id": ObjectId(metadata_id)}
        )

        if not metadata:
            return jsonify({"error": "File metadata not found"}), 404

        gridfs_id = metadata.get("gridfs_id")

        if gridfs_id:
            try:
                # --- Delete the file from GridFS ---
                fs.delete(gridfs_id)
                print(f"Successfully deleted GridFS file: {gridfs_id}")
            except Exception as gridfs_error:
                print(
                    f"Warning: Metadata {metadata_id} deleted, but failed to delete GridFS file {gridfs_id}: {gridfs_error}"
                )
        return jsonify({"message": "File deleted successfully"}), 200  # OK

    except Exception as e:
        print(f"Error deleting file metadata: {e}")
        return jsonify({"error": str(e)}), 500
