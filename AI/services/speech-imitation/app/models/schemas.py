import uuid
from dataclasses import dataclass, field
from enum import Enum


class SpeakerLabel(str, Enum):
    ADULT = "adult"
    CHILD = "child"
    UNKNOWN = "unknown"


class MatchPolicy(str, Enum):
    ALTERNATING = "alternating"
    PROTOCOL_BASED = "protocol_based"


class Severity(str, Enum):
    PASS = "PASS"
    WARN = "WARN"
    FAIL = "FAIL"


class FailureCode(str, Enum):
    # System / Pre-processing
    NO_SPEECH_DETECTED = "NO_SPEECH_DETECTED"
    INSUFFICIENT_STIMULUS = "INSUFFICIENT_STIMULUS"

    # Matching
    NO_RESPONSE = "NO_RESPONSE"  # No speech at all in window
    NO_CHILD_CANDIDATE = "NO_CHILD_CANDIDATE"  # Speech exists but not child

    # Quality / Candidates
    LOW_SNR = "LOW_SNR"
    MULTI_SPEAKER = "MULTI_SPEAKER"
    UNRELIABLE_VOICE_QUALITY = "UNRELIABLE_VOICE_QUALITY"

    # Scoring
    LOW_SIMILARITY = "LOW_SIMILARITY"
    BAD_PROSODY = "BAD_PROSODY"

    # Etc
    UNKNOWN_ERROR = "UNKNOWN_ERROR"


@dataclass
class SegmentSchema:
    """
    Physical/Acoustic properties of a speech segment.
    """

    segment_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    start_s: float = 0.0
    end_s: float = 0.0
    speaker_label: SpeakerLabel = SpeakerLabel.UNKNOWN

    # Acoustic Features
    energy_db: float | None = None  # dBFS
    f0_median_hz: float | None = None
    voiced_fraction: float | None = None  # 0.0 ~ 1.0 (voicing rate)
    jitter_local_pct: float | None = None
    shimmer_local_pct: float | None = None
    hnr_db: float | None = None

    # Reliability Flags
    quality_flags: list[str] = field(default_factory=list)


@dataclass
class PairSchema:
    """
    Represents a Stimulus-Response pair within a Trial.
    """

    pair_id: str  # e.g. "trial_01_rep_01"

    # Protocol Timings
    trial_index: int
    trial_start_s: float
    trial_end_s: float

    response_window_start_s: float
    response_window_end_s: float

    # Stimulus (Anchor)
    stimulus: SegmentSchema

    # Response (Target)
    response: SegmentSchema | None = None

    # Evaluation
    is_success: bool = False
    failure_code: FailureCode | None = None
    severity: Severity = Severity.PASS

    # Scores
    similarity_score: float | None = None
    overlap_ratio: float | None = None  # if applicable
