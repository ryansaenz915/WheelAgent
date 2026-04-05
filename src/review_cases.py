from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List

from .storage import DATA_DIR, read_json
from .validation import validate_case_fixture


@lru_cache(maxsize=1)
def _queue_path() -> Path:
    return DATA_DIR / "review_queue.json"


@lru_cache(maxsize=1)
def load_review_queue() -> List[Dict[str, Any]]:
    rows = read_json(_queue_path())
    if not isinstance(rows, list):
        raise ValueError("review_queue.json must be a list")
    return rows


@lru_cache(maxsize=32)
def load_case_by_id(review_id: str) -> Dict[str, Any]:
    queue = load_review_queue()
    for item in queue:
        if item["review_id"] == review_id:
            case_path = Path(__file__).resolve().parents[1] / item["case_file"]
            case = read_json(case_path)
            ok, msg = validate_case_fixture(case)
            if not ok:
                raise ValueError(f"Invalid case fixture {review_id}: {msg}")
            return case
    raise KeyError(f"Unknown review_id: {review_id}")


def load_all_cases() -> List[Dict[str, Any]]:
    return [load_case_by_id(item["review_id"]) for item in load_review_queue()]


def clear_case_cache() -> None:
    load_review_queue.cache_clear()
    load_case_by_id.cache_clear()
