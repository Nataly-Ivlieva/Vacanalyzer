import pandas as pd
from unittest.mock import patch, MagicMock
from functions.data_loader import load_jobs


@patch("functions.load_jobs.Job.select")
def test_load_jobs_with_data(mock_select):
    """
    Test case: load_jobs returns a DataFrame with valid data.
    
    - We mock the Peewee ORM query to return one fake job entry.
    - The function should convert the query into a pandas DataFrame.
    - The "date" column should be converted to datetime.
    """

    # Fake query result
    mock_query = MagicMock()
    mock_query.dicts.return_value = [
        {
            "date": "2025-09-08",
            "title": "Python Developer",
            "company": "ExampleCo",
            "salary_is_predicted": 0,
            "redirect_url": "http://example.com",
            "latitude": 52.52,
            "longitude": 13.405,
            "city": "Berlin",
            "district": None,
            "tech": "Python"
        }
    ]

    # Make Job.select() return our mock query
    mock_select.return_value = mock_query

    # Run the function
    df = load_jobs()

    # Assertions
    assert isinstance(df, pd.DataFrame)
    assert not df.empty
    assert "title" in df.columns
    assert df.loc[0, "title"] == "Python Developer"
    assert pd.api.types.is_datetime64_any_dtype(df["date"])  # check datetime parsing


@patch("functions.load_jobs.Job.select")
def test_load_jobs_empty(mock_select):
    """
    Test case: load_jobs should handle an empty query result.
    
    - We mock the Peewee ORM query to return an empty list.
    - The function should return an empty DataFrame without errors.
    """

    # Fake empty query
    mock_query = MagicMock()
    mock_query.dicts.return_value = []

    mock_select.return_value = mock_query

    df = load_jobs()

    # Assertions
    assert isinstance(df, pd.DataFrame)
    assert df.empty  # should be empty