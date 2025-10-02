# -*- encoding: utf-8 -*-


import os

from flask import Flask, session, flash
from flask_sqlalchemy import SQLAlchemy
from importlib import import_module


def register_extensions(app):
    return


def register_blueprints(app):
    for module_name in ("pages", "pages.authentication", "pages.jobs"):
        module = import_module("apps.{}.routes".format(module_name))
        app.register_blueprint(module.blueprint)


def create_app(config):
    app = Flask(__name__)
    app.config.from_object(config)

    @app.before_request
    def handle_toast_messages():
        """
        Checks the session for a toast message and flashes it.
        This runs before every request for the entire application.
        """
        try:
            if session.get("toastMessage"):
                # Flash the message from the session
                flash(
                    session["toastMessage"],
                    category=session.get("toastCategory", "info"),
                )
                # Clear the message from the session to prevent it from showing again
                session.pop("toastMessage", None)
                session.pop("toastCategory", None)
        except Exception as e:
            pass

    register_extensions(app)
    register_blueprints(app)
    return app
