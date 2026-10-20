"""Small date and time helpers."""
from datetime import timedelta

from .config import HOUR_BLOCKS


def stamp(dt):
    return dt.isoformat(timespec="seconds")


def hour_block(dt):
    return [label for start, label in HOUR_BLOCKS if dt.hour >= start][-1]


def add_business_days(d, n):
    while n > 0:
        d += timedelta(days=1)
        if d.weekday() < 5:
            n -= 1
    return d
