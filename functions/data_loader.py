import pandas as pd
from models.Job import Job
from models.JobLocation import JobLocation
from models.Tech import Tech
from models.Location import Location


def load_jobs():
    """
    Load job records from the database into a pandas DataFrame.

    The function:
    - Queries the database using Peewee ORM.
    - Joins job records with their related location and technology.
    - Filters out jobs where:
        * The technology is "Other"
        * The location is "Deutschland"
    - Converts the result into a pandas DataFrame.
    - Ensures the `date` column is parsed as datetime.

    Returns:
        pandas.DataFrame: A DataFrame containing job postings with the following columns:
            - date (datetime64[ns])
            - title (str): Job title
            - company (str): Company name
            - salary_is_predicted (bool/int): Whether the salary is predicted
            - redirect_url (str): URL to the job posting
            - latitude (float): Latitude of the job location
            - longitude (float): Longitude of the job location
            - city (str): City of the job
            - district (str | None): District (if available)
            - tech (str): Technology name
    """
    query = (
        Job
        .select(
            Job.date,
            Job.title,
            Job.company,
            Job.salary_is_predicted,
            Job.redirect_url,
            JobLocation.latitude,
            JobLocation.longitude,
            Location.display_name.alias('city'),
            JobLocation.district,
            Tech.name.alias('tech')
        )
        .join(JobLocation)
        .join(Location)
        .switch(Job)
        .join(Tech)
        .where(
            Tech.name != "Other",
            Location.display_name != "Deutschland"
        )
    )

    # Convert the query results to a DataFrame
    df = pd.DataFrame(list(query.dicts()))

    # Parse date column into datetime format
    df['date'] = pd.to_datetime(df['date'])

    return df