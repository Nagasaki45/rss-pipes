from datetime import datetime, time, timezone
from zoneinfo import ZoneInfo

import pytest

from rss_pipes.schedule import Frequency, Schedule, apply_schedule, generate_occurrences


@pytest.mark.parametrize(
    "schedule_str, expected",
    [
        ("daily-9:00", {"frequency": Frequency.DAILY, "time": time(9, 0), "day": None}),
        (
            "weekly-mon-15:00",
            {"frequency": Frequency.WEEKLY, "day": "mon", "time": time(15, 0)},
        ),
    ],
)
def test_valid_schedule(schedule_str, expected):
    schedule = Schedule.validate(schedule_str)
    assert schedule.frequency == expected["frequency"]
    assert schedule.time == expected["time"]
    assert schedule.day == expected["day"]


@pytest.mark.parametrize(
    "schedule_str, error_type, error_message",
    [
        (123, TypeError, "Schedule must be a string"),
        ("invalid-format", ValueError, "Invalid schedule format"),
        ("daily-25:00", ValueError, "Invalid time format"),
        ("weekly-9:00", ValueError, "Weekly schedule must specify a day"),
        ("weekly-1-9:00", ValueError, "Invalid weekly day"),
    ],
)
def test_invalid_schedule(schedule_str, error_type, error_message):
    with pytest.raises(error_type, match=error_message):
        Schedule.validate(schedule_str)


@pytest.mark.parametrize(
    "schedule, start_date, occurrences",
    [
        # Daily
        (
            Schedule.validate("daily-9:00"),
            datetime(2025, 1, 27, 0, 0),
            [
                datetime(2025, 1, 27, 9, 0),
                datetime(2025, 1, 28, 9, 0),
                datetime(2025, 1, 29, 9, 0),
                # ...
            ],
        ),
        # Weekly
        (
            Schedule.validate("weekly-fri-9:00"),
            datetime(2025, 1, 30, 8, 0),  # This is Thursday
            [
                datetime(2025, 1, 31, 9, 0),
                datetime(2025, 2, 7, 9, 0),
                datetime(2025, 2, 14, 9, 0),
                # ...
            ],
        ),
        # Timezone aware
        (
            Schedule.validate("daily-9:00"),
            datetime(2025, 1, 27, 0, 0, tzinfo=ZoneInfo("America/Los_Angeles")),
            [
                datetime(2025, 1, 27, 9, 0, tzinfo=ZoneInfo("America/Los_Angeles")),
                datetime(2025, 1, 28, 9, 0, tzinfo=ZoneInfo("America/Los_Angeles")),
                datetime(2025, 1, 29, 9, 0, tzinfo=ZoneInfo("America/Los_Angeles")),
                # ...
            ],
        ),
    ],
)
def test_generate_occurrences(schedule, start_date, occurrences):
    gen = generate_occurrences(schedule, start_date)
    for expected, result in zip(occurrences, gen):
        assert expected == result


@pytest.mark.parametrize(
    "schedule, items, expected",
    [
        (
            Schedule.validate("daily-9:00"),
            [
                (datetime(2025, 1, 1, 0, 0), "HNY"),
                (datetime(2025, 1, 1, 7, 0), "Wake up"),
                (datetime(2025, 1, 1, 12, 0), "Lunch"),
                (datetime(2025, 1, 1, 23, 0), "Bedtime"),
                (datetime(2025, 1, 2, 10, 0), "Oops, missed the alarm"),
            ],
            [
                (
                    datetime(2025, 1, 1, 9, 0),
                    [
                        (datetime(2025, 1, 1, 0, 0), "HNY"),
                        (datetime(2025, 1, 1, 7, 0), "Wake up"),
                    ],
                ),
                (
                    datetime(2025, 1, 2, 9, 0),
                    [
                        (datetime(2025, 1, 1, 12, 0), "Lunch"),
                        (datetime(2025, 1, 1, 23, 0), "Bedtime"),
                    ],
                ),
                (
                    datetime(2025, 1, 3, 9, 0),
                    [
                        (datetime(2025, 1, 2, 10, 0), "Oops, missed the alarm"),
                    ],
                ),
            ],
        ),
    ],
)
def test_apply_schedule(schedule, items, expected):
    assert apply_schedule(schedule, items) == expected
