import click
import datetime
from flask.cli import with_appcontext
from .pages.database import get_db


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
