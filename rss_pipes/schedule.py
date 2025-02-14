from datetime import datetime, time, timedelta
from enum import Enum
from typing import Iterator, assert_never, cast

from pydantic import BaseModel

_VALID_WEEK_DAYS = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]


class Frequency(str, Enum):
    DAILY = "daily"
    WEEKLY = "weekly"


def _parse_schedule_string(v: str) -> tuple[Frequency, time, str | int | None]:
    parts = v.split("-")

    # Parse frequency
    try:
        frequency = Frequency(parts[0])
    except ValueError:
        raise ValueError("Invalid schedule format")

    day: str | int | None = None
    # Parse based on frequency
    if frequency == Frequency.DAILY:
        if len(parts) != 2:
            raise ValueError("Invalid schedule format")

    elif frequency == Frequency.WEEKLY:
        if len(parts) != 3:
            raise ValueError("Weekly schedule must specify a day")
        day = parts[1].lower()
        if day not in _VALID_WEEK_DAYS:
            raise ValueError("Invalid weekly day")

    else:
        assert_never(frequency)

    # Parse time
    try:
        hour, minute = map(int, parts[-1].split(":"))
        schedule_time = time(hour, minute)
    except ValueError:
        raise ValueError("Invalid time format")

    return frequency, schedule_time, day


class Schedule(BaseModel):
    frequency: Frequency
    time: time
    day: str | int | None

    @classmethod
    def validate(cls, value: str) -> "Schedule":
        if not isinstance(value, str):
            raise TypeError("Schedule must be a string")

        frequency, schedule_time, day = _parse_schedule_string(value)
        return cls(frequency=frequency, time=schedule_time, day=day)

    def __str__(self) -> str:
        if self.frequency == Frequency.DAILY:
            return f"{self.frequency}-{self.time:%H:%M}"
        return f"{self.frequency}-{self.day}-{self.time:%H:%M}"


def _generate_daily_occurrences(
    schedule: Schedule, start_time: datetime
) -> Iterator[datetime]:
    scheduled_time = start_time.replace(
        hour=schedule.time.hour, minute=schedule.time.minute
    )
    if scheduled_time >= start_time:
        yield scheduled_time
    while True:
        scheduled_time += timedelta(days=1)
        yield scheduled_time


def _generate_weekly_occurrences(
    schedule: Schedule, start_time: datetime
) -> Iterator[datetime]:
    weekday_map = {day: i for i, day in enumerate(_VALID_WEEK_DAYS)}
    target_weekday = weekday_map[schedule.day]  # type: ignore[index] # day is str for weekly

    scheduled_time = start_time.replace(
        hour=schedule.time.hour, minute=schedule.time.minute
    )

    while scheduled_time.weekday() != target_weekday:
        scheduled_time += timedelta(days=1)

    while True:
        yield scheduled_time
        scheduled_time += timedelta(days=7)


def generate_occurrences(
    schedule: Schedule, start_date: datetime
) -> Iterator[datetime]:
    """Generate datetime occurrences for a schedule, working forwards from start_date."""
    if schedule.frequency == Frequency.DAILY:
        yield from _generate_daily_occurrences(schedule, start_date)
    elif schedule.frequency == Frequency.WEEKLY:
        yield from _generate_weekly_occurrences(schedule, start_date)
    else:
        assert_never(schedule.frequency)


def apply_schedule[T](
    schedule: Schedule, items: list[tuple[datetime, T]]
) -> list[tuple[datetime, list[tuple[datetime, T]]]]:
    """
    Take a schedule and a list of (datetime, item) pairs, group the items
    into occurrences by the schedule, and return the new groups, one per occurrence.
    """
    if not items:
        return []

    # Sort items by datetime
    sorted_items = sorted(items, key=lambda x: x[0])

    # Generate occurrences starting from earliest item
    occurrences = generate_occurrences(schedule, sorted_items[0][0])

    result = []
    current_group: list[tuple[datetime, T]] = []
    next_occurrence = next(occurrences)

    # Group items between occurrences
    for item_time, item in sorted_items:
        while item_time >= next_occurrence:
            if current_group:
                result.append((next_occurrence, current_group))
                current_group = []
            next_occurrence = next(occurrences)
        current_group.append((item_time, item))

    # Add final group if any items remain
    if current_group:
        result.append((next_occurrence, current_group))

    return result
