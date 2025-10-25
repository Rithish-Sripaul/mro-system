from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash,
    Response,
)
from apps.pages.database import get_db
from apps.pages.authentication.routes import login_required
from bson.objectid import ObjectId
import datetime
import json
from gridfs import GridFS
from gridfs.errors import NoFile  # NEW: Import NoFile for specific error handling
from werkzeug.utils import secure_filename

blueprint = Blueprint("inventory", __name__, url_prefix="/inventory")


@blueprint.route("/create-raw-material", methods=["GET", "POST"])
@login_required
def create_raw_material():
    db = get_db()

    # --- Centralized Database Collection Variables ---
    raw_materials_collection = db.raw_materials
    categories_collection = db.raw_material_categories
    suppliers_collection = db.raw_material_suppliers
    # -------------------------------------------------

    if request.method == "POST":
        # --- Process Form Data ---
        material_name = request.form.get("material_name")
        sku = request.form.get("sku")
        description = request.form.get("description")
        uom = request.form.get("uom")
        initial_quantity = float(request.form.get("initial_quantity", 0))
        reorder_level = float(request.form.get("reorder_level", 0))

        # Process Tagify inputs
        categories_str = request.form.get("categories", "[]")
        suppliers_str = request.form.get("suppliers", "[]")

        try:
            categories = [tag["value"] for tag in json.loads(categories_str)]
            suppliers = [tag["value"] for tag in json.loads(suppliers_str)]
        except json.JSONDecodeError:
            categories = []
            suppliers = []

        # --- Basic Validation ---
        if not all([material_name, sku, uom]):
            flash("Material Name, SKU, and Unit of Measure are required.", "error")
            # Re-render form with existing data if needed
            return redirect(url_for("inventory.create_raw_material"))

        # --- Handle Image Upload ---
        image_id = None
        if "material_image" in request.files:
            image_file = request.files["material_image"]
            if image_file and image_file.filename != "":
                if not image_file.content_type.startswith("image/"):
                    flash("Invalid file type. Please upload an image.", "error")
                    return redirect(url_for("inventory.create_raw_material"))

                fs = GridFS(db)
                filename = secure_filename(image_file.filename)
                image_id = fs.put(
                    image_file,
                    filename=filename,
                    content_type=image_file.content_type,
                    context="raw_material_image",
                )

        # Check for unique SKU
        if raw_materials_collection.find_one({"sku": sku}):
            flash(f"SKU '{sku}' already exists. Please use a unique SKU.", "error")
            return redirect(url_for("inventory.create_raw_material"))

        # Add new categories/suppliers to their respective collections
        if categories:
            for category_name in categories:
                # Increment count for the category, or create it with a count of 1 if it's new
                categories_collection.update_one(
                    {"name": category_name}, {"$inc": {"count": 1}}, upsert=True
                )
        if suppliers:
            for supplier_name in suppliers:
                # Increment count for the supplier, or create it with a count of 1 if it's new
                suppliers_collection.update_one(
                    {"name": supplier_name}, {"$inc": {"count": 1}}, upsert=True
                )

        # Insert the new raw material
        now = datetime.datetime.now()
        material_doc = {
            "material_name": material_name,
            "sku": sku,
            "description": description,
            "uom": uom,
            "current_quantity": initial_quantity,
            "reorder_level": reorder_level,
            "categories": categories,
            "suppliers": suppliers,
            "image_id": image_id,  # Store the GridFS file ID
            "created_at": now,
            "updated_at": now,
            "last_stocked_on": now,  # Set initial stock date
        }
        raw_materials_collection.insert_one(material_doc)

        # TODO: If initial_quantity > 0, create an entry in an 'inventory_log' collection.

        flash(f"Successfully created raw material: {material_name}", "success")
        return redirect(
            url_for("inventory.create_raw_material")
        )  # Or redirect to a manage page

    # --- Prepare data for GET request ---
    uom_list = [
        "kg",
        "grams",
        "meters",
        "mm",
        "liters",
        "units",
        "pairs",
        "sheets",
        "spools",
    ]
    categories_list = [
        doc["name"] for doc in categories_collection.find({}, {"name": 1})
    ]
    suppliers_list = [doc["name"] for doc in suppliers_collection.find({}, {"name": 1})]

    return render_template(
        "pages/inventory/create-raw-material.html",
        uom_list=uom_list,
        categories_whitelist=json.dumps(categories_list),
        suppliers_whitelist=json.dumps(suppliers_list),
    )


@blueprint.route("/image/<image_id>")
def get_raw_material_image(image_id):
    """Serves a raw material image from GridFS."""
    db = get_db()
    fs = GridFS(db)
    try:
        # Validate ObjectId format
        if not ObjectId.is_valid(image_id):
            print(f"DEBUG: Invalid ObjectId format for image_id: {image_id}")
            return "Invalid image ID format", 400

        oid = ObjectId(image_id)
        gridfs_file = fs.get(ObjectId(image_id))

        response = Response(gridfs_file.read(), mimetype=gridfs_file.content_type)
        response.headers["Content-Length"] = gridfs_file.length
        # Cache for 1 hour
        response.headers["Cache-Control"] = "public, max-age=3600"
        return response
    except NoFile:  # NEW: Specific error for file not found
        print(f"DEBUG: GridFS file not found for ID: {image_id}")
        return "File not found in GridFS", 404
    except Exception:
        # Return a 404 or a default placeholder image if not found
        return (
            "Internal server error",
            500,
        )  # NEW: More generic error for other exceptions


@blueprint.route("/manage-raw-materials", methods=["GET"])
@login_required
def manage_raw_materials():
    """
    Renders the page to display and manage all raw materials in a sortable,
    filterable table.
    """
    db = get_db()

    # --- Centralized Database Collection Variables ---
    raw_materials_collection = db.raw_materials
    categories_collection = db.raw_material_categories
    suppliers_collection = db.raw_material_suppliers
    # -------------------------------------------------

    # --- Fetch all raw materials for the table ---
    raw_materials_list = list(
        raw_materials_collection.find({}).sort("last_stocked_on", -1)
    )
    # NEW: Convert ObjectId to string for image_id for easier URL generation in template
    for material in raw_materials_list:
        if material.get("image_id"):
            material["image_id"] = str(material["image_id"])

    # --- Get data for filters ---

    # 1. Get all unique categories
    all_categories = categories_collection.distinct("name")
    all_categories = sorted([c for c in all_categories if c])

    # 2. Get all unique suppliers
    all_suppliers = suppliers_collection.distinct("name")
    all_suppliers = sorted([s for s in all_suppliers if s])

    # 3. Get all unique UoMs
    all_uoms = raw_materials_collection.distinct("uom")
    all_uoms = sorted([u for u in all_uoms if u])

    # --- Compute statistics for dashboard cards ---
    stats = {
        "total": len(raw_materials_list),
        "in_stock": 0,
        "above_reorder_level": 0,  # New stat
        "out_of_stock": 0,
        "below_reorder_level": 0,
    }

    for material in raw_materials_list:
        current_quantity = material.get("current_quantity", 0)
        reorder_level = material.get("reorder_level", 0)

        if current_quantity > 0:
            stats["in_stock"] += 1
        else:
            stats["out_of_stock"] += 1

        if current_quantity <= reorder_level:
            stats["below_reorder_level"] += 1
        else:  # current_quantity > reorder_level
            stats["above_reorder_level"] += 1

    return render_template(
        "pages/inventory/manage-raw-materials.html",
        raw_materials_list=raw_materials_list,
        all_categories=all_categories,
        all_suppliers=all_suppliers,
        all_uoms=all_uoms,
        stats=stats,
    )
