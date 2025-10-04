import os
import click
import datetime
import json
from pymongo import MongoClient
from flask import Blueprint, Response, current_app, flash, g
from functools import wraps
from flask import session, redirect, url_for, render_template, request
from apps.pages.authentication.routes import login_required
from apps.pages.database import get_db


blueprint = Blueprint("helper", __name__, url_prefix="/helper")


# Get schedule position
@blueprint.route("/get_schedule_position", methods=["POST", "GET"])
@login_required
def get_schedule_position():
    db = get_db()
    jobs_collection = db["jobs"]

    schedule_type = request.args.get("schedule_type")

    if not schedule_type:
        return Response(
            json.dumps({"error": "No schedule type provided"}),
            400,
            mimetype="application/json",
        )

    count = jobs_collection.count_documents({"schedule_type": schedule_type})
    next_position = count + 1

    print(f"Next position for schedule type '{schedule_type}': {next_position}")

    return Response(
        json.dumps({"next_position": next_position}), 200, mimetype="application/json"
    )
