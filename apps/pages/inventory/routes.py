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


blueprint = Blueprint("inventory", __name__, url_prefix="/inventory")
