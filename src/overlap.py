from __future__ import annotations

from datetime import date, timedelta
from typing import Tuple


def end_date(start_date: date, days_supply: int) -> date:
    if days_supply <= 0:
        return start_date
    return start_date + timedelta(days=days_supply - 1)


def overlap_days(start_a: date, end_a: date, start_b: date, end_b: date) -> int:
    overlap_start = max(start_a, start_b)
    overlap_end = min(end_a, end_b)
    delta = (overlap_end - overlap_start).days + 1
    return max(0, delta)


def pending_window(start_date: date, days_supply: int) -> Tuple[date, date]:
    return start_date, end_date(start_date, days_supply)


def calculate_supply_end_date(fill_date: date, days_supply: int) -> date:
    return end_date(fill_date, days_supply)


def inclusive_overlap_days(start_a: date, end_a: date, start_b: date, end_b: date) -> int:
    return overlap_days(start_a, end_a, start_b, end_b)
