# services/name_non_facing/app/models/speaker_diarizer.py
"""
화자 분리 (Speaker Diarization) 모듈

pyannote-audio를 사용하여 오디오에서 화자를 분리하고,
부모/아이 화자를 식별합니다.

Reference:
    - GitHub: https://github.com/pyannote/pyannote-audio
    - Paper: https://arxiv.org/abs/2306.03801
    - HuggingFace: https://huggingface.co/pyannote/speaker-diarization-3.1

Note:
    pyannote 모델 사용을 위해 HuggingFace 토큰이 필요합니다.
    1. https://huggingface.co/pyannote/speaker-diarization-3.1 접속
    2. 사용 조건 동의
    3. 토큰을 DIARIZATION_USE_AUTH_TOKEN 환경변수로 설정

pyannote-audio 선정 이유:

| 특성             | 설명                                          | 출처                                                         |
| ---------------- | --------------------------------------------- | ------------------------------------------------------------ |
| SOTA 성능    | 화자 분리 분야 최고 수준 정확도               | [pyannote 3.0 Paper](https://arxiv.org/abs/2306.03801)       |
| End-to-End   | VAD → 임베딩 → 클러스터링 파이프라인 통합     | [GitHub](https://github.com/pyannote/pyannote-audio)         |
| 화자 수 제어 | min/max speakers 파라미터로 화자 수 제한 가능 | [Documentation](https://github.com/pyannote/pyannote-audio#speaker-diarization) |
| 실시간 지원  | 스트리밍 모드 지원                            | -                                                            |

부모/아이 식별 전략:

1. 음성 특성 기반: 성인과 아동의 기본 주파수(F0) 차이 활용
   - 성인 남성: 85-180 Hz
   - 성인 여성: 165-255 Hz  
   - 아동: 250-400 Hz
   - 출처: [Voice Frequency Ranges](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC3562236/)

2. 발화 패턴 기반: 호명 검출 시 화자를 부모로 추정
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any
import logging

import numpy as np
import torch

from app.config import get_settings
from app.models.base import BaseModel

logger = logging.getLogger(__name__)


class SpeakerLabel(str, Enum):
    """화자 라벨"""
    PARENT = "parent"
    CHILD = "child"
    UNKNOWN = "unknown"


@dataclass
class SpeakerSegment:
    """화자별 발화 구간"""
    speaker_id: str              # 원본 화자 ID (SPEAKER_00 등)
    speaker_label: SpeakerLabel  # 식별된 라벨 (parent/child)
    start_sec: float             # 시작 시점 (초)
    end_sec: float               # 종료 시점 (초)
    
    @property
    def duration_sec(self) -> float:
        return self.end_sec - self.start_sec
    
    def __repr__(self) -> str: # 디버깅용. 예쁘게.
        return (
            f"SpeakerSegment({self.speaker_label.value}: "
            f"{self.start_sec:.2f}s ~ {self.end_sec:.2f}s)"
        )


@dataclass
class DiarizationResult:
    """화자 분리 결과"""
    segments: List[SpeakerSegment] = field(default_factory=list)
    speaker_mapping: Dict[str, SpeakerLabel] = field(default_factory=dict)
    num_speakers: int = 0
    
    def get_segments_by_label(self, label: SpeakerLabel) -> List[SpeakerSegment]:
        """특정 화자 라벨의 구간만 반환"""
        return [s for s in self.segments if s.speaker_label == label]
    
    def get_segments_in_range(
        self, 
        start_sec: float, 
        end_sec: float,
        label: Optional[SpeakerLabel] = None
    ) -> List[SpeakerSegment]:
        """특정 시간 범위 내 구간 반환"""
        filtered = []
        for seg in self.segments:
            # 범위와 겹치는지 확인
            if seg.end_sec > start_sec and seg.start_sec < end_sec:
                if label is None or seg.speaker_label == label:
                    filtered.append(seg)
        return filtered
    
    def get_total_duration_by_label(self, label: SpeakerLabel) -> float:
        """특정 화자의 총 발화 시간"""
        return sum(seg.duration_sec for seg in self.get_segments_by_label(label))


class SpeakerDiarizer(BaseModel):
    """
    pyannote-audio 기반 화자 분리기
    
    Usage:
        diarizer = SpeakerDiarizer()
        result = diarizer.diarize(audio, sample_rate=16000)
        
        # 부모 발화 구간
        parent_segments = result.get_segments_by_label(SpeakerLabel.PARENT)
        
        # 특정 시간 범위 내 아이 발화
        child_in_range = result.get_segments_in_range(
            start_sec=5.0, end_sec=10.0, label=SpeakerLabel.CHILD
        )
    
    Reference:
        https://github.com/pyannote/pyannote-audio#tldr
    """
    
    def __init__(self):
        """초기화"""
        self._settings = get_settings()
    
    def _load_model(self) -> None:
        """
        pyannote 파이프라인 로드
        
        Reference: https://github.com/pyannote/pyannote-audio#tldr
        """
        logger.info("🫡 pyannote 화자 분리 파이프라인 로딩...")
        
        try:
            from pyannote.audio import Pipeline
            
            # HuggingFace 모델 로드
            # Reference: https://huggingface.co/pyannote/speaker-diarization-3.1
            # Note: pyannote-audio 3.1+ uses 'token' instead of 'use_auth_token'
            self._model = Pipeline.from_pretrained(
                "pyannote/speaker-diarization-3.1",
                token=self._settings.DIARIZATION_USE_AUTH_TOKEN
            )
            
            # GPU 사용 설정
            if torch.cuda.is_available() and self._settings.DIARIZATION_DEVICE == "cuda":
                self._model.to(torch.device("cuda"))
                logger.info("🫡 pyannote GPU 모드로 실행")
            else:
                logger.info("🫡 pyannote CPU 모드로 실행")
            
            logger.info("🫡 pyannote 파이프라인 로드 완료")
            
        except Exception as e:
            logger.error(f"pyannote 로드 실패: {e}")
            raise RuntimeError(
                "😭 pyannote 모델 로드에 실패했습니다. "
                "DIARIZATION_USE_AUTH_TOKEN 환경변수를 확인하세요. "
                "HuggingFace에서 모델 사용 동의가 필요합니다: "
                "https://huggingface.co/pyannote/speaker-diarization-3.1"
            ) from e
    
    def predict(
        self,
        audio: np.ndarray,
        sample_rate: int = None
    ) -> DiarizationResult:
        """
        화자 분리 수행 (BaseModel 인터페이스)
        
        Args:
            audio: 오디오 데이터
            sample_rate: 샘플레이트
            
        Returns:
            DiarizationResult: 화자 분리 결과
        """
        return self.diarize(audio, sample_rate)
    
    def diarize(
        self,
        audio: np.ndarray,
        sample_rate: int = None,
        identify_speakers: bool = True,
        name_call_time: Optional[float] = None
    ) -> DiarizationResult:
        """
        화자 분리 수행
        
        Args:
            audio: 오디오 데이터 (numpy array, mono)
            sample_rate: 샘플레이트
            identify_speakers: 부모/아이 자동 식별 여부
            name_call_time: 호명 시점 (부모 식별 힌트로 활용)
            
        Returns:
            DiarizationResult: 화자 분리 결과
        """
        self.ensure_loaded()
        
        if sample_rate is None:
            sample_rate = self._settings.AUDIO_SAMPLE_RATE
        
        # numpy to torch tensor 변환 및 형식 맞추기
        if isinstance(audio, np.ndarray):
            audio_tensor = torch.from_numpy(audio).float()
        else:
            audio_tensor = audio
        
        # (samples,) → (1, samples) 형태로 변환
        if audio_tensor.dim() == 1:
            audio_tensor = audio_tensor.unsqueeze(0)
        
        # pyannote 입력 형식: {"waveform": tensor, "sample_rate": int}
        audio_input = {
            "waveform": audio_tensor,
            "sample_rate": sample_rate
        }
        
        # 화자 분리 실행
        # Reference: https://github.com/pyannote/pyannote-audio#speaker-diarization
        diarization_result = self._model(
            audio_input,
            min_speakers=self._settings.DIARIZATION_MIN_SPEAKERS,
            max_speakers=self._settings.DIARIZATION_MAX_SPEAKERS
        )
        
        # 결과 파싱
        # Note: pyannote-audio 3.1+ returns DiarizeOutput object
        segments = []
        speaker_ids = set()
        
        # DiarizeOutput 객체 처리
        # pyannote-audio 3.1+: DiarizeOutput has .speaker_diarization attribute
        if hasattr(diarization_result, 'speaker_diarization'):
            annotation = diarization_result.speaker_diarization
        elif hasattr(diarization_result, 'itertracks'):
            # 이전 버전: 직접 annotation 객체
            annotation = diarization_result
        else:
            logger.error(f"지원하지 않는 diarization 결과 타입: {type(diarization_result)}")
            raise TypeError(
                f"지원하지 않는 diarization 결과 타입: {type(diarization_result)}. "
                f"Annotation 또는 .speaker_diarization 속성이 필요합니다."
            )
        
        # Annotation 객체를 iteration
        for segment, _, speaker in annotation.itertracks(yield_label=True):
            if segment.duration < self._settings.DIARIZATION_MIN_SEGMENT_DURATION:
                continue
                
            seg = SpeakerSegment(
                speaker_id=speaker,
                speaker_label=SpeakerLabel.UNKNOWN,
                start_sec=segment.start,
                end_sec=segment.end
            )
            segments.append(seg)
            speaker_ids.add(speaker)
        
        # 시간순 정렬
        segments.sort(key=lambda s: s.start_sec)
        
        result = DiarizationResult(
            segments=segments,
            num_speakers=len(speaker_ids)
        )
        
        # 부모/아이 식별
        if identify_speakers and len(speaker_ids) >= 2:
            self._identify_parent_child(
                result, audio, sample_rate, name_call_time
            )
        
        logger.info(
            f"화자 분리 완료: {len(segments)}개 구간, "
            f"{len(speaker_ids)}명 화자"
        )
        
        return result
    
    def _identify_parent_child(
        self,
        result: DiarizationResult,
        audio: np.ndarray,
        sample_rate: int,
        name_call_time: Optional[float] = None
    ) -> None:
        """
        부모/아이 화자 식별
        
        식별 전략:
        1. 호명 시점에 발화 중인 화자 → 부모
        2. (호명 정보 없는 경우) 기본 주파수(F0) 분석 → 낮으면 부모
        
        Reference:
            음성 주파수 범위:
            - 성인 남성: 85-180 Hz
            - 성인 여성: 165-255 Hz
            - 아동: 250-400 Hz
            출처: https://www.ncbi.nlm.nih.gov/pmc/articles/PMC3562236/
        
        Args:
            result: 화자 분리 결과
            audio: 오디오 데이터
            sample_rate: 샘플레이트
            name_call_time: 호명 시점 (선택)
        """
        if not result.segments:
            return
        
        speaker_ids = list(set(seg.speaker_id for seg in result.segments))
        
        if len(speaker_ids) < 2:
            # 화자가 1명인 경우: UNKNOWN으로 유지
            return
        
        parent_id = None
        
        # 전략 1: 호명 시점 기반 식별
        if name_call_time is not None:
            for seg in result.segments:
                if seg.start_sec <= name_call_time <= seg.end_sec:
                    parent_id = seg.speaker_id
                    logger.debug(f"호명 시점 기반 부모 식별: {parent_id}")
                    break
        
        # 전략 2: F0 (기본 주파수) 기반 식별
        if parent_id is None:
            parent_id = self._identify_by_pitch(
                result.segments, audio, sample_rate, speaker_ids
            )
        
        # 매핑 생성
        if parent_id is not None:
            result.speaker_mapping[parent_id] = SpeakerLabel.PARENT
            for sid in speaker_ids:
                if sid != parent_id:
                    result.speaker_mapping[sid] = SpeakerLabel.CHILD
            
            # 세그먼트 라벨 업데이트
            for seg in result.segments:
                seg.speaker_label = result.speaker_mapping.get(
                    seg.speaker_id, SpeakerLabel.UNKNOWN
                )
    
    def _identify_by_pitch(
        self,
        segments: List[SpeakerSegment],
        audio: np.ndarray,
        sample_rate: int,
        speaker_ids: List[str]
    ) -> Optional[str]:
        """
        기본 주파수(F0) 분석을 통한 화자 식별
        
        성인(부모)과 아동의 평균 F0 차이를 활용:
        - 성인: 85-255 Hz (남녀 평균)
        - 아동: 250-400 Hz
        
        Returns:
            부모로 추정되는 화자 ID (낮은 F0)
        """
        try:
            import librosa
            
            speaker_pitches: Dict[str, List[float]] = {sid: [] for sid in speaker_ids}
            
            for seg in segments:
                # 각 구간에서 F0 추출
                start_sample = int(seg.start_sec * sample_rate)
                end_sample = int(seg.end_sec * sample_rate)
                segment_audio = audio[start_sample:end_sample]
                
                if len(segment_audio) < sample_rate * 0.1:  # 최소 0.1초
                    continue
                
                # F0 추출 (librosa.pyin)
                # Reference: https://librosa.org/doc/latest/generated/librosa.pyin.html
                f0, voiced_flag, _ = librosa.pyin(
                    segment_audio.astype(float),
                    fmin=50,    # 최소 주파수
                    fmax=500,   # 최대 주파수 (아동 포함)
                    sr=sample_rate
                )
                
                # 유성음 구간의 평균 F0
                voiced_f0 = f0[voiced_flag]
                if len(voiced_f0) > 0:
                    mean_f0 = np.nanmean(voiced_f0)
                    if not np.isnan(mean_f0):
                        speaker_pitches[seg.speaker_id].append(mean_f0)
            
            # 각 화자의 평균 F0 계산
            speaker_mean_f0 = {}
            for sid, pitches in speaker_pitches.items():
                if pitches:
                    speaker_mean_f0[sid] = np.mean(pitches)
            
            if len(speaker_mean_f0) >= 2:
                # F0가 낮은 화자 = 부모
                parent_id = min(speaker_mean_f0, key=speaker_mean_f0.get)
                logger.debug(
                    f"🫡 F0 기반 부모 식별: {parent_id} "
                    f"(F0: {speaker_mean_f0[parent_id]:.1f} Hz)"
                )
                return parent_id
                
        except ImportError:
            logger.warning("😭 librosa 미설치로 F0 기반 화자 식별 불가")
        except Exception as e:
            logger.warning(f"😭 F0 기반 화자 식별 실패: {e}")
        
        return None
    
    def get_speaker_turns(
        self,
        result: DiarizationResult
    ) -> List[Tuple[float, float, SpeakerLabel]]:
        """
        화자 전환 목록 반환 (시각화용)
        
        Returns:
            List[(start, end, label)]: 시간순 정렬된 화자 구간
        """
        return [
            (seg.start_sec, seg.end_sec, seg.speaker_label)
            for seg in result.segments
        ]