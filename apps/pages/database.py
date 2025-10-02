import os
import click
from pymongo import MongoClient
from flask import current_app, g


def get_db():

    if "db_client" not in g:
        g.db_client = MongoClient(current_app.config["MONGO_URI"])

    return g.db_client.get_database()
