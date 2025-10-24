import click
import datetime
import random
from faker import Faker  # Import Faker
from flask.cli import with_appcontext
from .pages.database import get_db
from bson.objectid import ObjectId


@click.command("seed-jobs")
@with_appcontext
def seed_jobs_command():
    """Clears existing jobs and adds 50 general and 50 priority test jobs."""
    db = get_db()
    jobs_collection = db["jobs"]
    users_collection = db["users"]
    divisions_collection = db["divisions"]

    # 1. Clear existing jobs for a clean slate
    jobs_collection.delete_many({})
    click.echo("Cleared existing jobs from the collection.")

    # 2. Fetch some real user and division IDs to use in the test data
    # This makes the test data more realistic
    sample_users = list(users_collection.find({}, {"_id": 1}).limit(2))
    sample_divisions = list(divisions_collection.find({}, {"_id": 1}).limit(2))

    if not sample_users or not sample_divisions:
        click.echo(
            "Warning: Could not find sample users or divisions. Test data will have empty lists for these fields."
        )
        user_ids = []
        division_ids = []
    else:
        user_ids = [user["_id"] for user in sample_users]
        division_ids = [div["_id"] for div in sample_divisions]

    jobs_to_create = []
    now = datetime.datetime.now()

    # 3. Create 50 General Schedule Jobs
    for i in range(1, 51):
        job = {
            "job_name": f"General Maintenance Task #{i}",
            "job_color": "#E91E63",
            "divisions": division_ids,
            "coordinators": user_ids,
            "description": f"This is a test description for general job number {i}.",
            "tags": ["testing", "general-schedule", f"task-{i}"],
            "status": "pending",
            "start_time": now,
            "completion_time": now + datetime.timedelta(days=i),
            "schedule_type": "general_schedule",
            "schedule_position": i,
            "created_at": now,
            "updated_at": now,
        }
        jobs_to_create.append(job)

    # 4. Create 50 Priority Schedule Jobs
    for i in range(1, 51):
        job = {
            "job_name": f"Priority Alert Response #{i}",
            "job_color": "#E91E63",
            "divisions": division_ids,
            "coordinators": user_ids,
            "description": f"This is a test description for priority job number {i}.",
            "tags": ["testing", "priority-schedule", f"alert-{i}"],
            "status": "pending",
            "start_time": now,
            "completion_time": now + datetime.timedelta(hours=i * 2),
            "schedule_type": "priority_schedule",
            "schedule_position": i,
            "created_at": now,
            "updated_at": now,
        }
        jobs_to_create.append(job)

    # 5. Insert all jobs into the database in one go (much faster)
    if jobs_to_create:
        jobs_collection.insert_many(jobs_to_create)
        click.echo(
            f"Successfully inserted {len(jobs_to_create)} test jobs into the database."
        )
    else:
        click.echo("No jobs were created.")


@click.command("seed-machines")
@click.option("--count", default=25, help="Number of machines to create.")
@click.option("--clear", is_flag=True, help="Clear existing machines before seeding.")
@with_appcontext
def seed_machines_command(count, clear):
    """Seeds the database with test machine data."""
    db = get_db()
    machines_collection = db["machines"]
    fake = Faker()  # Initialize Faker

    if clear:
        machines_collection.delete_many({})
        click.echo("Cleared existing machines from the collection.")

    machines_to_create = []
    now = datetime.datetime.now()

    # Define some sample data pools
    statuses = ["operating", "idle", "under_maintenance", "out_of_service"]
    criticalities = ["high", "medium", "low"]
    manufacturers = [
        "Siemens",
        "Fanuc",
        "ABB",
        "Rockwell",
        "Mitsubishi",
        "Omron",
        "Kuka",
    ]
    tags_pool = [
        "CNC",
        "Robot",
        "PLC",
        "Sensor",
        "Motor",
        "Pump",
        "HVAC",
        "Compressor",
        "Conveyor",
    ]
    meter_units = ["hours", "cycles", "units"]
    time_units = ["days", "weeks", "months"]

    for i in range(count):
        # Generate basic info
        machine_name = f"{fake.word().capitalize()} Machine {i+1}"
        asset_id = f"ASSET-{random.randint(1000, 9999)}-{i}"
        manufacturer = random.choice(manufacturers)
        model_number = f"{manufacturer[:3].upper()}-{random.randint(100, 999)}"
        current_status = random.choice(statuses)
        criticality = random.choice(criticalities)
        tags = random.sample(tags_pool, k=random.randint(1, 3))  # 1 to 3 random tags
        installation_date = fake.date_time_between(start_date="-3y", end_date="-1y")
        warranty_expiry_date = (
            fake.date_time_between(start_date="+1y", end_date="+3y")
            if random.random() > 0.3
            else None
        )  # 70% chance of having warranty

        # Generate maintenance schedule (50/50 time vs usage)
        maintenance_schedule = {}
        if random.random() > 0.5:
            # Time-based
            gap = random.choice([30, 60, 90, 180])
            unit = random.choice(time_units)
            next_date = now + datetime.timedelta(
                days=random.randint(1, gap)
            )  # Schedule next PM within the gap
            maintenance_schedule = {
                "trigger": "time_based",
                "time_gap": gap,
                "time_gap_unit": unit,
                "next_maintenance_date": next_date,
            }
        else:
            # Usage-based
            gap = random.choice([100, 500, 1000, 5000])
            unit = random.choice(meter_units)
            current_reading = random.uniform(
                0, gap * 5
            )  # Current reading up to 5 cycles past due
            maintenance_schedule = {
                "trigger": "usage_based",
                "usage_gap": gap,
                "meter_unit": unit,
                "current_meter_reading": round(current_reading, 2),
            }

        # Generate optional notes
        notes = (
            fake.paragraph(nb_sentences=3) if random.random() > 0.6 else None
        )  # 40% chance of notes

        # Assemble the machine document
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
            "operation_id": None,  # Placeholder
            "number_of_operations": 0,  # Placeholder
            "notes": notes,
            "file_metadata_ids": [],  # Placeholder - seeding files is more complex
            "created_at": fake.date_time_between(
                start_date="-6m", end_date="now"
            ),  # Vary creation time slightly
            "updated_at": now,
        }
        machines_to_create.append(machine_data)

    # Insert all machines
    if machines_to_create:
        machines_collection.insert_many(machines_to_create)
        click.echo(f"Successfully inserted {len(machines_to_create)} test machines.")
    else:
        click.echo("No machines were created.")
