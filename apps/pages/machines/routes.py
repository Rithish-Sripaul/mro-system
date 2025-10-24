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

# --- Import json_util for data response ---
from bson import json_util

blueprint = Blueprint("machines", __name__, url_prefix="/machines")


@blueprint.route("/manage-machines", methods=["GET"])
@login_required
def manage_machines():
    """
    Renders the page to display and manage all machines in a sortable,
    filterable table.
    """
    db = get_db()
    machines_collection = db["machines"]

    # --- Fetch all machines for the table ---
    machines_list = list(machines_collection.find({}).sort("created_at", -1))

    # --- Get data for filters ---

    # 1. Get all unique tags from the entire collection
    all_tags = machines_collection.distinct("tags")
    all_tags = sorted(
        [tag for tag in all_tags if tag]
    )  # Filter out None/empty and sort

    # 2. Define the static status list for the filter
    status_list = [
        {"value": "operating", "name": "Operating"},
        {"value": "idle", "name": "Idle"},
        {"value": "under_maintenance", "name": "Under Maintenance"},
        {"value": "out_of_service", "name": "Out of Service"},
    ]

    # --- Compute statistics for dashboard cards ---
    stats = {
        "total": len(machines_list),
        "operating": 0,
        "idle": 0,
        "maintenance": 0,
        "out_of_service": 0,
        "high_criticality": 0,
    }

    for machine in machines_list:
        # Count statuses
        status = machine.get("current_status")
        if status == "operating":
            stats["operating"] += 1
        elif status == "idle":
            stats["idle"] += 1
        elif status == "under_maintenance":
            stats["maintenance"] += 1
        elif status == "out_of_service":
            stats["out_of_service"] += 1

        # Count high criticality
        if machine.get("criticality") == "high":
            stats["high_criticality"] += 1

    return render_template(
        "pages/machines/manage.html",
        machines_list=machines_list,
        all_tags=all_tags,
        status_list=status_list,
        stats=stats,
    )


@blueprint.route("/create-machines", methods=["GET", "POST"])
@login_required  # Protect this route
def create_machines():
    db = get_db()
    fs = GridFS(db)
    machines_collection = db["machines"]
    files_metadata_collection = db["machine_files_metadata"]

    if request.method == "POST":
        try:
            # === 1. GET FORM DATA ===
            machine_name = request.form.get("machine_name")
            asset_id = request.form.get("asset_id")
            current_status = request.form.get("current_status")
            criticality = request.form.get("criticality")
            manufacturer = request.form.get("manufacturer")
            model_number = request.form.get("model_number")
            notes = request.form.get("notes")  # From Quill's hidden input

            # === 2. HANDLE TAGS (from Tagify JSON) ===
            tags_json_string = request.form.get("tags")
            tags = []
            if tags_json_string:
                try:
                    tags_data = json.loads(tags_json_string)
                    tags = [tag["value"] for tag in tags_data if "value" in tag]
                except json.JSONDecodeError:
                    tags = []  # Fail silently if JSON is bad

            # === 3. HANDLE DATES ===
            installation_date_str = request.form.get("installation_date")
            warranty_expiry_date_str = request.form.get("warranty_expiry_date")

            date_format = "%m/%d/%Y"  # Based on our daterangepicker config

            installation_date = None
            if installation_date_str:
                installation_date = datetime.datetime.strptime(
                    installation_date_str, date_format
                )

            warranty_expiry_date = None
            if warranty_expiry_date_str:
                warranty_expiry_date = datetime.datetime.strptime(
                    warranty_expiry_date_str, date_format
                )

            # === 4. HANDLE CONDITIONAL MAINTENANCE SCHEDULE ===
            maintenance_trigger = request.form.get("maintenance_trigger")
            maintenance_schedule = {
                "trigger": maintenance_trigger,
            }

            if maintenance_trigger == "time_based":
                maintenance_schedule["time_gap"] = request.form.get(
                    "time_gap", type=int
                )
                maintenance_schedule["time_gap_unit"] = request.form.get(
                    "time_gap_unit"
                )
                next_maintenance_date_str = request.form.get("next_maintenance_date")
                maintenance_schedule["next_maintenance_date"] = None
                if next_maintenance_date_str:
                    maintenance_schedule["next_maintenance_date"] = (
                        datetime.datetime.strptime(
                            next_maintenance_date_str, date_format
                        )
                    )

            elif maintenance_trigger == "usage_based":
                maintenance_schedule["usage_gap"] = request.form.get(
                    "usage_gap", type=int
                )
                maintenance_schedule["meter_unit"] = request.form.get("meter_unit")
                maintenance_schedule["current_meter_reading"] = request.form.get(
                    "current_meter_reading", type=float
                )

            # === 5. HANDLE FILE UPLOADS ===
            uploaded_file_metadata_ids = []  # To store in the machine document
            files = request.files.getlist("attachments")

            for file in files:
                if file and file.filename:  # Check if a file was actually selected
                    original_filename = secure_filename(file.filename)
                    content_type = file.content_type

                    # 1. Save file to GridFS
                    gridfs_file_id = fs.put(
                        file,  # The file stream
                        filename=original_filename,
                        content_type=content_type,
                        uploader_user_id=ObjectId(session["user_id"]),
                    )

                    # 2. Get file info (for size/date)
                    gridfs_file_info = fs.get(gridfs_file_id)

                    # 3. Save METADATA to our new collection
                    file_metadata = {
                        "machine_id": None,  # Will update this after machine is created
                        "gridfs_id": gridfs_file_id,
                        "original_filename": original_filename,
                        "content_type": content_type,
                        "size": gridfs_file_info.length,
                        "upload_timestamp": gridfs_file_info.upload_date,
                        "uploader_user_id": ObjectId(session["user_id"]),
                        "uploader_username": session["user_name"],
                    }

                    result = files_metadata_collection.insert_one(file_metadata)

                    # 4. Store the NEW metadata ID
                    uploaded_file_metadata_ids.append(result.inserted_id)

            # === 6. ASSEMBLE AND INSERT THE MACHINE DOCUMENT ===
            machine_data = {
                "machine_name": machine_name,
                "asset_id": asset_id,
                "current_status": current_status,
                "criticality": criticality,
                "tags": tags,
                "manufacturer": manufacturer,
                "model_number": model_number,
                "installation_date": installation_date,
                "warranty_expiry_date": warranty_expiry_date,
                "maintenance_schedule": maintenance_schedule,
                "operation_id": None,
                "number_of_operations": 0,
                "notes": notes,
                "file_metadata_ids": uploaded_file_metadata_ids,  # Link to metadata
                "created_at": datetime.datetime.now(),
                "updated_at": datetime.datetime.now(),
            }

            machine_result = machines_collection.insert_one(machine_data)
            new_machine_id = machine_result.inserted_id

            # === 7. (Optional but good practice) UPDATE METADATA ===
            # Add the new machine_id to all the metadata documents we just created
            if uploaded_file_metadata_ids:
                files_metadata_collection.update_many(
                    {"_id": {"$in": uploaded_file_metadata_ids}},
                    {"$set": {"machine_id": new_machine_id}},
                )

            flash(f"Machine '{machine_name}' created successfully!", "success")
            return redirect(url_for("machines.create_machines"))

        except Exception as e:
            print(f"Error creating machine: {e}")
            flash(f"An error occurred: {e}", "danger")

    # --- GET Request Logic ---
    # Pass necessary data to the form (like dropdown lists)

    # This list is needed for the "Meter Unit" dropdown
    meter_units_list = [
        {"value": "hours", "name": "Hours"},
        {"value": "cycles", "name": "Cycles"},
        {"value": "units", "name": "Units Produced"},
    ]

    machines_list = list(
        machines_collection.find(
            {}, {"asset_id": 1, "machine_name": 1, "current_status": 1}
        ).sort("asset_id", 1)
    )

    return render_template(
        "pages/machines/create.html",
        meter_units_list=meter_units_list,
        machines_list=machines_list,
    )


@blueprint.route("/details/<string:machine_id>", methods=["GET"])
@login_required
def machine_details(machine_id):
    """
    Displays the full details page for a single machine.
    """
    db = get_db()
    machines_collection = db["machines"]
    files_metadata_collection = db["machine_files_metadata"]

    # --- Fetch the machine ---
    machine = machines_collection.find_one({"_id": ObjectId(machine_id)})
    if not machine:
        flash("Machine not found.", "danger")
        return redirect(url_for("machines.manage_machines"))

    # --- Fetch associated files ---
    files_list = list(
        files_metadata_collection.find({"machine_id": ObjectId(machine_id)}).sort(
            "upload_timestamp", -1
        )
    )

    # --- Fetch operation history (empty for now) ---
    operations_list = []

    # --- Get status list for the dropdown ---
    status_list = [
        {"value": "operating", "name": "Operating"},
        {"value": "idle", "name": "Idle"},
        {"value": "under_maintenance", "name": "Under Maintenance"},
        {"value": "out_of_service", "name": "Out of Service"},
    ]

    # --- Calculate upcoming maintenance schedule ---
    upcoming_maintenance = []
    schedule = machine.get("maintenance_schedule", {})
    trigger = schedule.get("trigger")

    if trigger == "time_based":
        next_date = schedule.get("next_maintenance_date")
        gap = schedule.get("time_gap")
        unit = schedule.get("time_gap_unit")

        if next_date and gap and unit:
            current_date = next_date
            for _ in range(5):  # Get next 5 dates
                upcoming_maintenance.append(current_date.strftime("%d %b, %Y"))
                if unit == "days":
                    current_date += datetime.timedelta(days=gap)
                elif unit == "weeks":
                    current_date += datetime.timedelta(weeks=gap)
                elif unit == "months":
                    # Simple month addition (doesn't account for end of month perfectly)
                    current_date = current_date.replace(day=1) + datetime.timedelta(
                        days=32 * gap
                    )
                    current_date = current_date.replace(day=min(next_date.day, 28))

    elif trigger == "usage_based":
        current_reading = schedule.get("current_meter_reading", 0)
        gap = schedule.get("usage_gap")
        unit = schedule.get("meter_unit")

        if current_reading is not None and gap and unit:
            next_due = (math.floor(current_reading / gap) + 1) * gap
            for i in range(5):  # Get next 5 readings
                upcoming_maintenance.append(f"At {int(next_due + (i * gap))} {unit}")

    return render_template(
        "pages/machines/machine-details.html",
        machine=machine,
        files_list=files_list,
        operations_list=operations_list,
        status_list=status_list,
        upcoming_maintenance=upcoming_maintenance,
    )


@blueprint.route("/files/<string:metadata_id>/download", methods=["GET"])
@login_required
def download_machine_file(metadata_id):
    """Allows downloading a specific file from GridFS."""
    try:
        db = get_db()
        fs = GridFS(db)
        files_metadata_collection = db["machine_files_metadata"]

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

        response = Response(gridfs_file, mimetype=gridfs_file.content_type)
        response.headers["Content-Length"] = gridfs_file.length
        response.headers["Content-Disposition"] = (
            f'attachment; filename="{gridfs_file.filename}"'
        )
        return response

    except Exception as e:
        print(f"Error downloading file from GridFS: {e}")
        return jsonify({"error": str(e)}), 500


# Update Machine Status
@blueprint.route("/update-status", methods=["POST"])
@login_required
def update_machine_status():
    """
    Handles AJAX request to update a machine's status.
    """
    db = get_db()
    machines_collection = db["machines"]

    try:
        data = request.get_json()
        machine_id = data.get("machine_id")
        new_status = data.get("new_status")

        if not machine_id or not new_status:
            return jsonify({"success": False, "error": "Missing data"}), 400

        # Validate status
        valid_statuses = ["operating", "idle", "under_maintenance", "out_of_service"]
        if new_status not in valid_statuses:
            return jsonify({"success": False, "error": "Invalid status value"}), 400

        # Perform the update
        result = machines_collection.update_one(
            {"_id": ObjectId(machine_id)},
            {
                "$set": {
                    "current_status": new_status,
                    "updated_at": datetime.datetime.now(),
                }
            },
        )

        if result.matched_count == 0:
            return jsonify({"success": False, "error": "Machine not found"}), 404

        return jsonify({"success": True, "new_status": new_status})

    except Exception as e:
        print(f"Error updating machine status: {e}")
        return jsonify({"success": False, "error": str(e)}), 500
