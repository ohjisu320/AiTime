from dataclasses import dataclass


@dataclass
class CallResult:
    call_index: int
    call_start: float
    call_end: float
    success: bool
    latency_s: float | None
    gaze_duration_s: float
