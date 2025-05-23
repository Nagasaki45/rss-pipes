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
        (
            "monthly-15-09:00",
            {"frequency": Frequency.MONTHLY, "day": 15, "time": time(9, 0)},
        ),
        (
            "monthly-31-23:59",
            {"frequency": Frequency.MONTHLY, "day": 31, "time": time(23, 59)},
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
        ("monthly-9:00", ValueError, "Monthly schedule must specify a day"),
        ("monthly-0-09:00", ValueError, "Monthly day must be between 1 and 31"),
        ("monthly-32-09:00", ValueError, "Monthly day must be between 1 and 31"),
        ("monthly-abc-09:00", ValueError, "Monthly day must be a number"),
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
        # Monthly - normal case
        (
            Schedule.validate("monthly-15-9:00"),
            datetime(2025, 1, 10, 0, 0),
            [
                datetime(2025, 1, 15, 9, 0),
                datetime(2025, 2, 15, 9, 0),
                datetime(2025, 3, 15, 9, 0),
                # ...
            ],
        ),
        # Monthly - day 31 in February (should use last day)
        (
            Schedule.validate("monthly-31-9:00"),
            datetime(2025, 2, 1, 0, 0),
            [
                datetime(2025, 2, 28, 9, 0),  # Feb 2025 has 28 days
                datetime(2025, 3, 31, 9, 0),
                datetime(2025, 4, 30, 9, 0),  # April has 30 days
                # ...
            ],
        ),
        # Monthly - leap year
        (
            Schedule.validate("monthly-29-9:00"),
            datetime(2024, 2, 1, 0, 0),  # 2024 is a leap year
            [
                datetime(2024, 2, 29, 9, 0),  # Feb 2024 has 29 days
                datetime(2024, 3, 29, 9, 0),
                datetime(2024, 4, 29, 9, 0),
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
        (
            Schedule.validate("monthly-15-9:00"),
            [
                (datetime(2025, 1, 5, 0, 0), "Early January"),
                (datetime(2025, 1, 10, 0, 0), "Mid January"),
                (datetime(2025, 1, 20, 0, 0), "Late January"),
                (datetime(2025, 2, 5, 0, 0), "Early February"),
                (datetime(2025, 2, 20, 0, 0), "Late February"),
            ],
            [
                (
                    datetime(2025, 1, 15, 9, 0),
                    [
                        (datetime(2025, 1, 5, 0, 0), "Early January"),
                        (datetime(2025, 1, 10, 0, 0), "Mid January"),
                    ],
                ),
                (
                    datetime(2025, 2, 15, 9, 0),
                    [
                        (datetime(2025, 1, 20, 0, 0), "Late January"),
                        (datetime(2025, 2, 5, 0, 0), "Early February"),
                    ],
                ),
                (
                    datetime(2025, 3, 15, 9, 0),
                    [
                        (datetime(2025, 2, 20, 0, 0), "Late February"),
                    ],
                ),
            ],
        ),
    ],
)
def test_apply_schedule(schedule, items, expected):
    assert apply_schedule(schedule, items) == expected
