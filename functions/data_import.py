import os
import requests
from dotenv import load_dotenv
import json
import time
from datetime import datetime
from functions.logger_config import logger


def fetch_jobs(sleep_func=time.sleep):
    """
    Fetch job vacancies from the Adzuna API and save them to a JSON file.

    The function:
    - Loads API credentials (ADZUNA_APP_ID, ADZUNA_APP_KEY) from environment variables.
    - Requests job postings page by page from the Adzuna API.
    - Collects all job results until there are no more pages available.
    - Saves the aggregated results into a JSON file with the current date in its name.

    Args:
        sleep_func (callable, optional): A function used to pause between requests 
                                         (default: time.sleep). This makes testing easier.

    Returns:
        str | None: 
            The filename of the saved JSON file if successful,
            or None if an error occurred.

    Raises:
        ValueError: If required environment variables (ADZUNA_APP_ID, ADZUNA_APP_KEY) are missing.
    """
    try:
        # Load environment variables
        load_dotenv()
        app_id = os.getenv("ADZUNA_APP_ID")
        app_key = os.getenv("ADZUNA_APP_KEY")

        if not app_id or not app_key:
            raise ValueError("ADZUNA_APP_ID or ADZUNA_APP_KEY is missing from the environment variables.")

        # Base API configuration
        url = "https://api.adzuna.com/v1/api/jobs/de/search/{}"
        what = "Softwareentwickler"
        category = "it-jobs"
        page = 1
        results_per_page = 50
        all_jobs = []

        # Pagination loop
        while True:
            params = {
                "app_id": app_id,
                "app_key": app_key,
                "what": what,
                "category": category,
                "results_per_page": results_per_page,
                "content-type": "application/json"
            }
            try:
                response = requests.get(url.format(page), params=params, timeout=10)
                response.raise_for_status()
            except requests.RequestException as e:
                logger.error(f"Request Error: {e}")
                break

            # Extract jobs from the response
            data = response.json()
            jobs = data.get("results", [])
            if not jobs:
                logger.info("No more jobs found, finishing pagination.")
                break

            all_jobs.extend(jobs)
            logger.info(f"Page loaded {page}, vacancies on the page: {len(jobs)}")

            page += 1
            sleep_func(1)  # Throttle requests

        print(f"Total vacancies loaded: {len(all_jobs)}")

        # Save results into a JSON file
        current_date = datetime.now().strftime("%Y-%m-%d")
        filename = f"all_jobs_{current_date}.json"

        try:
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(all_jobs, f, indent=4, ensure_ascii=False)
        except IOError as e:
            logger.error(f"Error writing file: {e}")
            return None

        return filename

    except Exception as e:
        logger.exception(f"An error occurred: {e}")
        return None