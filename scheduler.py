import schedule
import time
from functions.database import create_tables, import_jobs_from_json
from functions.data_import import fetch_jobs
from functions.logger_config import logger


def job():
    """
    Scheduled job for importing vacancies:
        1. Fetch jobs from the Adzuna API and save them to a JSON file.
        2. Ensure all database tables exist.
        3. Import the jobs into the database from the saved JSON file.
    """
    logger.info("Vacancy import started...")
    filename = fetch_jobs()
    if not filename:
        logger.error("Job fetching failed. Skipping import.")
        return

    create_tables()
    import_jobs_from_json(filename)

    logger.info("Vacancy import finished successfully!")


# Schedule the job every day at 22:30
schedule.every().day.at("22:30").do(job)

logger.info("Scheduler started. Waiting for scheduled jobs...")

# Keep the scheduler running
while True:
    schedule.run_pending()
    time.sleep(1)