from datetime import date

from src.overlap import end_date, overlap_days


def test_end_date_30_day_fill_is_inclusive():
    assert end_date(date(2026, 3, 1), 30) == date(2026, 3, 30)


def test_overlap_days_zero_when_no_intersection():
    assert overlap_days(
        date(2026, 3, 20),
        date(2026, 6, 17),
        date(2026, 2, 10),
        date(2026, 3, 9),
    ) == 0


def test_overlap_days_is_11_for_sample_same_strength_fill():
    assert overlap_days(
        date(2026, 3, 20),
        date(2026, 6, 17),
        date(2026, 3, 1),
        date(2026, 3, 30),
    ) == 11
