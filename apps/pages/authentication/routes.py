import os
import click
import datetime
from pymongo import MongoClient
from flask import Blueprint, current_app, flash, g
from functools import wraps
from flask import session, redirect, url_for, render_template, request
from werkzeug.security import generate_password_hash, check_password_hash
from apps.pages.database import get_db

blueprint = Blueprint("authentication", __name__, url_prefix="/auth")


# ------------------ LOGIN --------------------------
@blueprint.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        db = get_db()
        users_collection = db["users"]

        # Handle login logic
        user_name = request.form.get("userName")
        user_password = request.form.get("userPassword")

        user = users_collection.find_one({"name": user_name})
        if user and check_password_hash(user["password"], user_password):
            session.clear()
            g.user = user["_id"]
            session["user_id"] = str(user["_id"])
            session["user_name"] = user["name"]
            session["is_master"] = user.get("is_master", False)

            session["toastMessage"] = "Login successful!"
            session["toastCategory"] = "success"
            return redirect(url_for("pages_blueprint.index"))
        else:
            session["toastMessage"] = "Invalid username or password"
            session["toastCategory"] = "alert"
            return redirect(url_for("authentication.login"))
    return render_template("pages/authentication/login.html")


# ------------------ LOGOUT --------------------------
@blueprint.route("/logout")
def logout():
    session.clear()
    session["toastMessage"] = "You have been logged out."
    session["toastCategory"] = "info"
    return redirect(url_for("authentication.login"))


@blueprint.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        db = get_db()
        users_collection = db["users"]

        user_name = request.form.get("userName")
        user_email = request.form.get("userEmail")
        user_password = request.form.get("userPassword")
        is_master = request.form.get("isMaster") == "on"

        # Checking if user already exists
        existing_user_email = users_collection.find_one({"email": user_email})
        existing_user = users_collection.find_one({"name": user_name})
        if existing_user:
            error = "User Name already exists. Please choose a different name."
            # Toast Message
            session["toastMessage"] = error
            session["toastCategory"] = "alert"
            return redirect(url_for("authentication.register"))
        if existing_user_email:
            error = "Email already registered. Please use a different email."
            session["toastMessage"] = error
            session["toastCategory"] = "alert"
            return redirect(url_for("authentication.register"))

        # Inserting new user
        users_collection.insert_one(
            {
                "name": user_name,
                "email": user_email,
                "password": generate_password_hash(user_password),
                "is_master": is_master,
                "created_at": datetime.datetime.now(),
                "updated_at": datetime.datetime.now(),
            }
        )

        # Redirect to login with success message
        session["toastMessage"] = "Registration successful! Please log in."
        session["toastCategory"] = "success"

        return redirect(url_for("authentication.login"))
    return render_template("pages/authentication/register.html")


@blueprint.before_app_request
def load_logged_in_user():
    user_id = session.get("user_id")

    if user_id is None:
        g.user = None
    else:
        g.user = user_id


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if g.user is None:
            return redirect(url_for("authentication.login"))
        return f(*args, **kwargs)

    return decorated_function
