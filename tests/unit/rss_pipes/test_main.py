from datetime import time
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from rss_pipes.main import app
from rss_pipes.schedule import Frequency, Schedule


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture()
def digest_feed_mock():
    with patch("rss_pipes.main.digest_feed") as mock:
        mock.return_value = "FAKE FEED"
        yield mock


def test_digest_happy_path(client, digest_feed_mock):
    # When
    response = client.get(
        f"/digest/https://example.org/atom.xml",
        params={"schedule": "daily-9:00"},
    )

    # Then
    assert response.status_code == 200

    digest_feed_mock.assert_called_once_with(
        "https://example.org/atom.xml",
        Schedule(frequency=Frequency.DAILY, time=time(hour=9), day=None),
    )


def test_digest_invalid_schedule(client):
    # When
    response = client.get(
        f"/digest/https://example.org/atom.xml",
        params={"schedule": "invalid-schedule"},
    )

    # Then
    assert response.status_code == 422
