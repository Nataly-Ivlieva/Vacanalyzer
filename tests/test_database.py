import pytest
from unittest.mock import patch, MagicMock
from functions.database import import_jobs_from_json, extract_tech


@pytest.mark.parametrize(
    "title,expected",
    [
        ("Senior Python Entwickler", "Python"),
        ("JavaScript Developer", "JavaScript"),
        ("Unknown Role", "Other"),
        ("Fullstack Java / Python Developer", "Java")  
    ]
)
def test_extract_tech(title, expected):
    """
    Test for the extract_tech function.

    Ensures that:
    - Known technologies (e.g., Python, JavaScript, Java) are detected correctly.
    - Unknown or irrelevant titles are classified as "Other".
    """
    assert extract_tech(title) == expected


@patch("functions.database.JobLocation")
@patch("functions.database.Location")
@patch("functions.database.Job")
@patch("functions.database.Tech")
@patch("builtins.open")
@patch("json.load")
def test_import_jobs_from_json(mock_json_load, mock_open, mock_tech, mock_job, mock_location, mock_job_location):
    """
    Test for the import_jobs_from_json function.

    This test uses mocks to simulate:
    - Reading job data from a JSON file.
    - Interactions with the database models (Tech, Job, Location, JobLocation).

    Validates that:
    - The JSON file is opened and read correctly.
    - Tech, Job, and Location records are created.
    - JobLocation is handled properly (created if not already present).
    """

    # Mock JSON content returned by json.load
    mock_json_load.return_value = [
        {
            "id": "job_1",
            "title": "Python Developer",
            "description": "Test job",
            "salary_is_predicted": "0",
            "redirect_url": "http://example.com",
            "company": {"display_name": "ExampleCo"},
            "location": {"display_name": "Berlin"},
            "latitude": 52.52,
            "longitude": 13.405
        }
    ]

    # Mock database model behaviors
    mock_tech.get_or_create.return_value = ("PythonObj", True)
    mock_job.get_or_create.return_value = ("JobObj", True)
    mock_location.get_or_create.return_value = ("BerlinObj", True)
    mock_job_location.select.return_value.where.return_value.first.return_value = None

    # Call the function under test
    import_jobs_from_json("all_jobs_2025-09-08.json")

    # Assertions to verify correct behavior
    mock_open.assert_called_once_with("all_jobs_2025-09-08.json", "r", encoding="utf-8")
    mock_json_load.assert_called_once()
    mock_tech.get_or_create.assert_called_with(name="Python")
    mock_job.get_or_create.assert_called()

