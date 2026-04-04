from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class AuditLogger:
    jsonl_path: Optional[Path] = None
    records: List[Dict[str, Any]] = field(default_factory=list)

    def log(self, event: str, details: Dict[str, Any]) -> None:
        record = {
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "event": event,
            "details": details,
        }
        self.records.append(record)
        if self.jsonl_path:
            self.jsonl_path.parent.mkdir(parents=True, exist_ok=True)
            with self.jsonl_path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(record) + "\n")
