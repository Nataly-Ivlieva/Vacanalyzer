from db import db
import json
import re
from datetime import datetime
from peewee import IntegrityError
from models.Job import Job
from models.Tech import Tech
from models.Location import Location
from models.JobLocation import JobLocation
from functions.logger_config import logger


def create_tables():
    """
    Create database tables for all defined models.

    Ensures that the database is connected and all necessary tables
    (Tech, Location, Job, JobLocation) are created if they do not exist.

    Logs:
        - Info: when tables are successfully created.
        - Exception: if table creation fails.
    """
    models = [Tech, Location, Job, JobLocation]
    try:
        if db.is_closed():
            db.connect()
        db.create_tables(models, safe=True)
        logger.info("Tables created successfully.")
    except Exception as e:
        logger.exception(f"Failed to create tables: {e}")


def extract_tech(title: str) -> str:
    """
    Extract the technology name from a job title.

    Args:
        title (str): Job title string.

    Returns:
        str: Detected technology (e.g., 'Python', 'JavaScript').
             Returns "Other" if no known technology is found.

    Logs:
        - Warning: if extraction fails due to unexpected error.
    """
    KNOWN_TECHS = {
        "SAP", "Clojure", "C#", "Java", "C++", "PHP", "Python", "JavaScript",
        "AWS", "VHDL", "COBOL", "RPG", "Delphi", "Angular", "TypeScript", "Go",
        "Ruby", "SQL", "PL/SQL", "ABAP", "NodeJS", "Flutter", "Scala", "Kotlin",
        "Rust", ".NET", "iOS", "Android"
    }
    IGNORE_WORDS = {
        "softwareentwickler", "entwickler", "entwicklerin", "entwickler/in",
        "software", "programmierer", "m/w/d", "mwd", ":in", "leiter",
        "teamleitung", "projektleiter", "senior", "junior", "fullstack",
        "praktikum", "student", "werkstudent", "trainee", "dual", "mit", "in", "als"
    }
    try:
        clean_title = re.sub(r"\(.*?\)|/.*?|[-,]", " ", title)
        words = clean_title.lower().split()
        for word in words:
            if word in IGNORE_WORDS:
                continue
            for tech in KNOWN_TECHS:
                if word == tech.lower():
                    return tech
    except Exception as e:
        logger.warning(f"Failed to extract tech from title '{title}': {e}")
    return "Other"


def import_jobs_from_json(json_path: str):
    """
    Import job postings from a JSON file into the database.

    Args:
        json_path (str): Path to the JSON file containing job postings.

    Behavior:
        - Extracts job date from filename if possible.
        - Reads jobs from JSON and inserts/updates them in the database.
        - Creates or updates related Tech, Job, Location, and JobLocation records.
        - Handles duplicates and updates existing entries if necessary.

    Logs:
        - Warning: if date extraction fails or integrity issues occur.
        - Error: if file is missing or JSON is invalid.
        - Exception: if unexpected errors occur during processing.
        - Info: when the import is completed successfully.
    """
    try:
        date_match = re.search(r"(\d{4}-\d{2}-\d{2})", json_path)
        job_date = datetime.strptime(date_match.group(1), "%Y-%m-%d").date() if date_match else None
        if job_date is None:
            logger.warning(f"Failed to extract date from {json_path}")

        with open(json_path, "r", encoding="utf-8") as f:
            jobs_data = json.load(f)

        for job_data in jobs_data:
            try:
                job_id = job_data.get("id")
                title = job_data.get("title", "")
                description = job_data.get("description", "")
                salary_is_predicted = job_data.get("salary_is_predicted") == "1"
                redirect_url = job_data.get("redirect_url", "")
                company = job_data.get("company", {}).get("display_name", "")
                tech_name = extract_tech(title) or "Other"
                tech, _ = Tech.get_or_create(name=tech_name)

                job, created = Job.get_or_create(
                    job_id=job_id,
                    defaults={
                        "title": title,
                        "description": description,
                        "salary_is_predicted": salary_is_predicted,
                        "redirect_url": redirect_url,
                        "company": company,
                        "tech": tech,
                        "date": job_date
                    }
                )

                if not created:
                    job.title = title
                    job.description = description
                    job.salary_is_predicted = salary_is_predicted
                    job.redirect_url = redirect_url
                    job.company = company
                    job.tech = tech
                    job.save()

                location_info = job_data.get("location", {})
                display_name = location_info.get("display_name")
                latitude = job_data.get("latitude")
                longitude = job_data.get("longitude")

                if display_name and display_name != "Deutschland":
                    parts = [p.strip() for p in display_name.split(",")]
                    if len(parts) == 2:
                        district_name, city_name = parts
                    else:
                        district_name, city_name = None, parts[0]

                    city_location, _ = Location.get_or_create(display_name=city_name)

                    job_loc_query = JobLocation.select().where(
                        (JobLocation.job == job) &
                        (JobLocation.location == city_location) &
                        ((JobLocation.district == district_name) |
                         (JobLocation.district.is_null() & (district_name is None)))
                    ).first()

                    if job_loc_query:
                        updated = False
                        if latitude is not None and job_loc_query.latitude != latitude:
                            job_loc_query.latitude = latitude
                            updated = True
                        if longitude is not None and job_loc_query.longitude != longitude:
                            job_loc_query.longitude = longitude
                            updated = True
                        if updated:
                            job_loc_query.save()
                    else:
                        JobLocation.create(
                            job=job,
                            location=city_location,
                            district=district_name,
                            latitude=latitude,
                            longitude=longitude
                        )
            except IntegrityError as ie:
                logger.warning(f"IntegrityError for job {job_data.get('id')}: {ie}")
            except Exception as e:
                logger.exception(f"Error processing job {job_data.get('id')}: {e}")

        logger.info("Job import completed successfully.")
    except FileNotFoundError:
        logger.error(f"JSON file not found: {json_path}")
    except json.JSONDecodeError:
        logger.error(f"Failed to decode JSON: {json_path}")
    except Exception as e:
        logger.exception(f"Unexpected error while importing jobs from {json_path}: {e}")