from pathlib import Path

import pytest

from rss_pipes.digest import digest_feed
from rss_pipes.schedule import Schedule

from .test_utils import normalize_xml_string

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.mark.asyncio
async def test_digest(httpx_mock):
    # Given
    with open(FIXTURES_DIR / "atom.xml") as f:
        input_feed = f.read()

    with open(FIXTURES_DIR / "weekly_atom.xml") as f:
        expected_output_feed = f.read()

    feed_url = "https://example.org/atom.xml"
    httpx_mock.add_response(url=feed_url, text=input_feed)
    schedule = Schedule.validate("weekly-sat-10:00")

    # When
    result = await digest_feed(feed_url, schedule)

    # Then
    assert normalize_xml_string(result) == normalize_xml_string(expected_output_feed)
