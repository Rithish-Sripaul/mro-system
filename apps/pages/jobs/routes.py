import os
import click
import datetime
from pymongo import MongoClient
from flask import Blueprint, current_app, flash, g
from functools import wraps
from flask import session, redirect, url_for, render_template, request
from apps.pages.database import get_db


blueprint = Blueprint("jobs", __name__, url_prefix="/jobs")


@blueprint.route("/manage_jobs")
def manage_jobs():
    db = get_db()
    users_collection = db["users"]
    divisions_collection = db["divisions"]

    user_list = list(users_collection.find({}, {"_id": 1, "name": 1}).sort("name", 1))
    divisions_list = list(
        divisions_collection.find({}, {"_id": 1, "name": 1}).sort("name", 1)
    )

    return render_template(
        "pages/jobs/manage_jobs.html",
        divisions_list=divisions_list,
        user_list=user_list,
    )
