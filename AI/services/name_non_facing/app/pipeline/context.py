# services/name_non_facing/app/pipeline/context.py
"""
파이프라인 컨텍스트 모듈

파이프라인 실행 중 상태를 공유하고, 단계 간 데이터를 전달합니다.
( 아이 이름을 부르는 영상 분석 AI가 작동하는 동안 모든 데이터를 한곳에 모아 관리하고, 최종 결과를 정리해주는 코드.)

역할: 
- 파이프라인 실행 상태 및 데이터 저장

핵심 필드:
| 필드               | 타입                     | 설명                |
| ------------------ | ------------------------ | ----------------- |
| `request_id`       | str                      | 요청 식별자        |
| `video_path`       | str                      | 입력 비디오 경로    |
| `child_name`       | str                      | 아이 이름          |
| `audio`            | np.ndarray               | 추출된 오디오       |
| `name_call_events` | List[NameCallEvent]      | 호명 이벤트 목록    |
| `voice_reactions`  | List[ChildVoiceReaction] | 음성 반응 목록      |
| `trial_results`    | List[TrialResult]        | 시도별 최종 결과    |
| `processing_times` | Dict[str, float]         | Stage별 처리 시간  |

설계 의도:
- `dataclass` 사용으로 불변성 지향 및 타입 안전성 확보
- `to_result()` 메서드로 일관된 출력 형식 보장
- 메타데이터(에러, 경고, 시간) 추적으로 디버깅 용이

설계 원칙:
    1. 단일 공급원
       - 모든 Stage가 동일한 Context 객체를 참조
       - 중간 결과와 최종 결과가 한 곳에 집약
       
    2. 불변성 지향
       - 입력 데이터는 수정하지 않음
       - 결과는 새 필드에 저장
       
    3. 추적 가능성
       - 각 Stage의 처리 시간, 에러, 경고 기록
       - 디버깅 및 모니터링 용이

Reference:
    - Context Object Pattern: https://wiki.c2.com/?ContextObject
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum

import numpy as np


class PipelineStatus(str, Enum):
    """파이프라인 실행 상태"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class TrialResult:
    """
    개별 Trial 결과
    
    호명 반응 검사에서 각 시도별 결과를 저장합니다.
    """
    trial_index: int                             # 시도 번호 (1-based)
    success: bool                                # 반응 성공 여부
    latency_s: Optional[float] = None            # 반응 지연 시간 (초)
    
    # 음성 반응 관련
    voice_detected: bool = False                 # 음성 반응 감지 여부
    voice_start_s: Optional[float] = None        # 음성 반응 시작 시점
    voice_end_s: Optional[float] = None          # 음성 반응 종료 시점
    voice_duration_s: Optional[float] = None     # 음성 반응 지속 시간
    voice_confidence: float = 0.0                # 음성 반응 신뢰도
    
    # 시선 반응 관련 (Vision Stage에서 채울 예정임.)
    gaze_match: bool = False                     # 시선 반응 여부
    gaze_duration_s: Optional[float] = None      # 시선 유지 시간
    head_yaw_deg: Optional[float] = None         # 고개 Yaw 회전 (도)
    head_pitch_deg: Optional[float] = None       # 고개 Pitch 회전 (도)
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리 변환"""
        return {
            "trial_index": self.trial_index,
            "success": self.success,
            "latency_s": self.latency_s,
            "voice_detected": self.voice_detected,
            "voice_start_s": self.voice_start_s,
            "voice_end_s": self.voice_end_s,
            "voice_duration_s": self.voice_duration_s,
            "voice_confidence": self.voice_confidence,
            "gaze_match": self.gaze_match,
            "gaze_duration_s": self.gaze_duration_s,
            "head_yaw_deg": self.head_yaw_deg,
            "head_pitch_deg": self.head_pitch_deg,
        }


@dataclass
class PipelineContext:
    """
    파이프라인 실행 컨텍스트
    
    모든 Stage가 공유하는 상태 객체입니다.
    입력 데이터, 중간 결과, 최종 결과, 메타데이터를 포함합니다.
    """
    
    # ===== 요청 정보 (필수) =====
    request_id: str
    video_path: str
    child_name: str
    child_nickname: Optional[str] = None
    
    # ===== 실행 상태 =====
    status: PipelineStatus = PipelineStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    
    # ===== 추출된 오디오 데이터 =====
    audio: Optional[np.ndarray] = None          # (samples,) float32
    sample_rate: int = 16000
    audio_duration_sec: float = 0.0
    audio_path: Optional[str] = None            # 임시 파일 경로
    
    # ===== 음성 인식 결과 =====
    # Type hints만 명시, 실제 타입은 순환 import 방지를 위해 Any 사용
    transcription: Optional[Any] = None         # TranscriptionResult
    name_call_events: List[Any] = field(default_factory=list)  # List[NameCallEvent]
    
    # ===== 화자 분리 결과 =====
    diarization: Optional[Any] = None           # DiarizationResult
    
    # ===== 음성 반응 결과 =====
    voice_reactions: List[Any] = field(default_factory=list)  # List[ChildVoiceReaction]
    
    # ===== 비전 결과 (향후 확장) =====
    frames: Optional[List[np.ndarray]] = None
    fps: float = 30.0
    parent_positions: List[Any] = field(default_factory=list)
    child_positions: List[Any] = field(default_factory=list)
    gaze_results: List[Any] = field(default_factory=list)
    
    # ===== 최종 결과 =====
    trial_results: List[TrialResult] = field(default_factory=list)
    
    # ===== 메타데이터 =====
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    processing_times: Dict[str, float] = field(default_factory=dict)
    
    def add_error(self, stage_name: str, message: str) -> None:
        """에러 추가"""
        self.errors.append(f"[{stage_name}] {message}")
    
    def add_warning(self, stage_name: str, message: str) -> None:
        """경고 추가"""
        self.warnings.append(f"[{stage_name}] {message}")
    
    def record_time(self, stage_name: str, elapsed_sec: float) -> None:
        """처리 시간 기록"""
        self.processing_times[stage_name] = elapsed_sec
    
    def to_result(self) -> Dict[str, Any]:
        """
        최종 결과 딕셔너리 생성
        
        Reference:
            - 필수참고_작업설계.md의 응답 json 양식
        """
        return {
            "request_id": self.request_id,
            "analyzed_at": (
                self.completed_at.isoformat() 
                if self.completed_at 
                else datetime.now().isoformat()
            ),
            "status": self.status.value,
            "metrics": {
                "per_trial": [tr.to_dict() for tr in self.trial_results]
            },
            "metadata": {
                "audio_duration_sec": self.audio_duration_sec,
                "num_trials": len(self.name_call_events),
                "processing_times": self.processing_times,
            },
            "errors": self.errors if self.errors else None,
            "warnings": self.warnings if self.warnings else None,
        }
