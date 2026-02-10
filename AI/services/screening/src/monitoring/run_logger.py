import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class JsonlRunLogger:
    run_id: str
    trace_id: str
    logs_dir: str
    enabled: bool = True

    def __post_init__(self) -> None:
        if not self.enabled:
            return
        Path(self.logs_dir).mkdir(parents=True, exist_ok=True)

    def log(self, event: str, payload: dict[str, Any]) -> None:
        if not self.enabled:
            return

        path = Path(self.logs_dir) / f"{self.run_id}.jsonl"
        rec = {
            "ts": _utc_now_iso(),
            "event": event,
            "run_id": self.run_id,
            "trace_id": self.trace_id,
            **payload,
        }

        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    def close(self) -> None:
        pass
