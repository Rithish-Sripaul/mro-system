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


@blueprint.route("/restock-raw-material", methods=["GET", "POST"])
@login_required
def restock_raw_material():
    """
    Renders a page to log a new stock purchase for raw materials and saves
    the record, including an uploaded bill.
    """
    db = get_db()
    raw_materials_collection = db.raw_materials
    suppliers_collection = db.raw_material_suppliers
    procurement_collection = (
        db.procurement_records
    )  # Collection for bills/restock events

    if request.method == "POST":
        # --- Process Form Data ---
        supplier_name = request.form.get("supplier_name")
        bill_number = request.form.get("bill_number")
        bill_date_str = request.form.get("bill_date")
        notes = request.form.get("notes")
        items_json = request.form.get("items_data")  # JSON string of items

        # --- Basic Validation ---
        if not all([supplier_name, bill_number, bill_date_str, items_json]):
            flash(
                "Supplier, Bill Number, Bill Date, and at least one item are required.",
                "error",
            )
            return redirect(url_for("inventory.restock_raw_material"))

        try:
            items = json.loads(items_json)
            bill_date = datetime.datetime.strptime(bill_date_str, "%Y-%m-%d")
        except (json.JSONDecodeError, ValueError):
            flash("Invalid item data or date format.", "error")
            return redirect(url_for("inventory.restock_raw_material"))

        # --- Handle Bill Upload ---
        bill_file_id = None
        if "bill_upload" in request.files:
            bill_file = request.files["bill_upload"]
            if bill_file and bill_file.filename != "":
                fs = GridFS(db)
                filename = secure_filename(bill_file.filename)
                bill_file_id = fs.put(
                    bill_file, filename=filename, content_type=bill_file.content_type
                )

        # --- Create Procurement Record ---
        now = datetime.datetime.now()
        procurement_doc = {
            "supplier_name": supplier_name,
            "bill_number": bill_number,
            "bill_date": bill_date,
            "bill_file_id": bill_file_id,
            "procurement_items": items,  # RENAMED: Contains material_id, quantity, unit_price
            "notes": notes,
            "created_at": now,
        }
        procurement_collection.insert_one(procurement_doc)

        # --- Update Stock Levels for each item ---
        for item in items:
            raw_materials_collection.update_one(
                {"_id": ObjectId(item["material_id"])},
                {
                    "$inc": {"current_quantity": float(item["quantity"])},
                    "$set": {"last_stocked_on": now},
                },
            )

        flash(f"Successfully logged stock from bill '{bill_number}'.", "success")
        return redirect(url_for("inventory.restock_raw_material"))

    # --- Prepare data for GET request ---
    all_materials = list(
        raw_materials_collection.find(
            {}, {"material_name": 1, "sku": 1, "uom": 1, "current_quantity": 1}
        )
    )
    for mat in all_materials:
        mat["_id"] = str(mat["_id"])  # Convert ObjectId to string for JS

    all_suppliers = sorted(
        [doc["name"] for doc in suppliers_collection.find({}, {"name": 1})]
    )

    # NEW: Fetch procurement history for the wizard's first tab
    procurement_history = list(procurement_collection.find({}).sort("bill_date", -1))
    for record in procurement_history:
        record["_id"] = str(record["_id"])
        if record.get("bill_file_id"):
            record["bill_file_id"] = str(record["bill_file_id"])
        # Calculate total amount for each bill
        total_amount = sum(
            item.get("quantity", 0) * item.get("unit_price", 0)
            for item in record["procurement_items"]
        )
        record["total_amount"] = total_amount
        # NEW: Fetch material names for display in the history table
        material_ids = [
            ObjectId(item["material_id"]) for item in record["procurement_items"]
        ]
        materials_in_bill = raw_materials_collection.find(
            {"_id": {"$in": material_ids}}, {"material_name": 1, "sku": 1}
        )
        material_map = {str(m["_id"]): m for m in materials_in_bill}
        for item in record["procurement_items"]:
            material_info = material_map.get(item["material_id"])
            if material_info:
                item["material_name"] = material_info.get("material_name", "N/A")
                item["sku"] = material_info.get("sku", "N/A")

    return render_template(
        "pages/inventory/restock-raw-material.html",
        all_materials_json=json.dumps(all_materials),
        all_suppliers=all_suppliers,
        procurement_history=procurement_history,
    )


@blueprint.route("/procurement-record/<record_id>")
@login_required
def procurement_record_detail(record_id):
    """
    Renders the detailed view for a single procurement record.
    """
    db = get_db()
    procurement_collection = db.procurement_records
    raw_materials_collection = db.raw_materials

    try:
        record = procurement_collection.find_one({"_id": ObjectId(record_id)})
    except Exception:
        record = None

    if not record:
        flash("Procurement record not found.", "error")
        return redirect(url_for("inventory.restock_raw_material"))

    # --- Enrich record data for display ---
    subtotal = 0
    for item in record.get("procurement_items", []):
        item_total = item.get("quantity", 0) * item.get("unit_price", 0)
        item["total_price"] = item_total
        subtotal += item_total

        # Fetch material details
        material_info = raw_materials_collection.find_one(
            {"_id": ObjectId(item["material_id"])},
            {"material_name": 1, "sku": 1, "description": 1},
        )
        if material_info:
            item["material_name"] = material_info.get("material_name", "N/A")
            item["sku"] = material_info.get("sku", "N/A")
            # For the "Product Details" part of the invoice
            item["description"] = f"SKU: {item['sku']}"

    record["subtotal"] = subtotal
    # For now, grand_total is the same as subtotal. Can be expanded later.
    record["grand_total"] = subtotal

    return render_template(
        "pages/inventory/procurement-raw-material-detail.html", record=record
    )


@blueprint.route("/procurement-record/<record_id>/edit", methods=["GET", "POST"])
@login_required
def edit_procurement_record(record_id):
    """
    Renders a page to edit an existing procurement record.
    """
    db = get_db()
    procurement_collection = db.procurement_records
    raw_materials_collection = db.raw_materials
    suppliers_collection = db.raw_material_suppliers

    try:
        record = procurement_collection.find_one({"_id": ObjectId(record_id)})
    except Exception:
        record = None

    if not record:
        flash("Procurement record not found.", "error")
        return redirect(url_for("inventory.restock_raw_material"))

    if request.method == "POST":
        # --- Get Original Items to Revert Stock ---
        original_items = record.get("procurement_items", [])

        # --- Process Form Data ---
        supplier_name = request.form.get("supplier_name")
        bill_number = request.form.get("bill_number")
        bill_date_str = request.form.get("bill_date")
        notes = request.form.get("notes")
        items_json = request.form.get("items_data")

        if not all([supplier_name, bill_number, bill_date_str, items_json]):
            flash(
                "Supplier, Bill Number, Bill Date, and at least one item are required.",
                "error",
            )
            return redirect(
                url_for("inventory.edit_procurement_record", record_id=record_id)
            )

        try:
            updated_items = json.loads(items_json)
            bill_date = datetime.datetime.strptime(bill_date_str, "%Y-%m-%d")
        except (json.JSONDecodeError, ValueError):
            flash("Invalid item data or date format.", "error")
            return redirect(
                url_for("inventory.edit_procurement_record", record_id=record_id)
            )

        # --- Revert Old Stock Quantities ---
        for item in original_items:
            raw_materials_collection.update_one(
                {"_id": ObjectId(item["material_id"])},
                {"$inc": {"current_quantity": -float(item["quantity"])}},
            )

        # --- Apply New Stock Quantities ---
        for item in updated_items:
            raw_materials_collection.update_one(
                {"_id": ObjectId(item["material_id"])},
                {
                    "$inc": {"current_quantity": float(item["quantity"])},
                    "$set": {
                        "last_stocked_on": datetime.datetime.now()
                    },  # Update stock date
                },
            )

        # --- Update Procurement Record ---
        # Note: Bill file is not handled here for simplicity. A more complex UI would be needed.
        update_data = {
            "supplier_name": supplier_name,
            "bill_number": bill_number,
            "bill_date": bill_date,
            "notes": notes,
            "procurement_items": updated_items,
            "updated_at": datetime.datetime.now(),
        }
        procurement_collection.update_one(
            {"_id": ObjectId(record_id)}, {"$set": update_data}
        )

        flash(
            f"Successfully updated procurement record for bill '{bill_number}'.",
            "success",
        )
        return redirect(
            url_for("inventory.procurement_record_detail", record_id=record_id)
        )

    # --- Prepare data for GET request ---
    # For the item selection dropdown
    all_materials = list(
        raw_materials_collection.find(
            {}, {"material_name": 1, "sku": 1, "uom": 1, "current_quantity": 1}
        )
    )
    for mat in all_materials:
        mat["_id"] = str(mat["_id"])

    # For the supplier dropdown
    all_suppliers = sorted(
        [doc["name"] for doc in suppliers_collection.find({}, {"name": 1})]
    )

    # Enrich items with material name for display in the form
    for item in record.get("procurement_items", []):
        material_info = raw_materials_collection.find_one(
            {"_id": ObjectId(item["material_id"])}, {"material_name": 1, "sku": 1}
        )
        if material_info:
            item["material_name"] = material_info.get("material_name", "N/A")
            item["sku"] = material_info.get("sku", "N/A")

    # Convert record data for template consumption
    record["_id"] = str(record["_id"])
    record["bill_date_str"] = record["bill_date"].strftime("%Y-%m-%d")

    return render_template(
        "pages/inventory/edit-procurement-record.html",
        record=record,
        all_materials_json=json.dumps(all_materials),
        all_suppliers=all_suppliers,
    )
