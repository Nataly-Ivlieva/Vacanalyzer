import json
import pytest
from unittest.mock import patch, mock_open
from functions.data_import import fetch_jobs

# Fake API response
mock_response = {
    "results": [
        {"title": "Softwareentwickler", "company": {"display_name": "ABC GmbH"}},
        {"title": "Junior Developer", "company": {"display_name": "XYZ AG"}}
    ]
}


@pytest.fixture
def mock_env(monkeypatch):
    """
    Pytest fixture that sets up environment variables
    for the Adzuna API.

    This ensures that the fetch_jobs function has
    valid APP_ID and APP_KEY during testing.
    """
    monkeypatch.setenv("ADZUNA_APP_ID", "fake_id")
    monkeypatch.setenv("ADZUNA_APP_KEY", "fake_key")


def test_fetch_jobs(mock_env):
    """
    Test for the fetch_jobs function.

    Validates that:
    1. The mocked API call returns the expected data.
    2. The function writes the results to a JSON file.
    3. The resulting file contains the expected number of jobs
       and correct job details.
    """

    class MockResponse:
        """Mocked response object for requests.get."""
        def __init__(self, json_data, status_code=200):
            self._json = json_data
            self.status_code = status_code

        def json(self):
            return self._json

        @property
        def ok(self):
            return self.status_code == 200

        def raise_for_status(self):
            if not self.ok:
                raise Exception(f"HTTP Error {self.status_code}")

    def mock_get(*args, **kwargs):
        """
        Mock implementation of requests.get.
        Returns job data on the first page and empty results afterwards.
        """
        page = int(args[0].split("/")[-1])
        if page > 1:
            return MockResponse({"results": []})
        return MockResponse(mock_response)

    m = mock_open()
    with patch("functions.data_import.requests.get", side_effect=mock_get), \
         patch("builtins.open", m):

        filename = fetch_jobs()
        assert filename is not None, "fetch_jobs() should return a filename"

        handle = m()
        written_data = "".join(call.args[0] for call in handle.write.call_args_list)
        data = json.loads(written_data)

        assert len(data) == 2
        assert data[0]["title"] == "Softwareentwickler"
