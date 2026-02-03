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
        pyannote 파이프라인 로드 (Lazy Loading)
        
        Note:
            - 이 메서드는 최초 1회만 실행됩니다 (싱글톤 + Lazy Loading)
            - 이후 호출은 메모리에 캐시된 모델을 재사용합니다
            - 로딩에 10-30초 정도 소요될 수 있습니다
        
        Reference: https://github.com/pyannote/pyannote-audio#tldr
        """
        logger.info("🔄 pyannote 화자 분리 파이프라인 로딩 중... (최초 1회, 10-30초 소요)")
        logger.info("💡 이후 호출부터는 캐시된 모델을 즉시 사용합니다")
        
        try:
            logger.debug("📦 HuggingFace 및 pyannote 라이브러리 import 중...")
            from huggingface_hub import login
            from pyannote.audio import Pipeline
            logger.debug("✅ 라이브러리 import 완료")
            
            # 토큰 상태 확인
            has_token = bool(self._settings.DIARIZATION_USE_AUTH_TOKEN)
            logger.info(f"🔑 HuggingFace 토큰 설정 여부: {has_token}")
            if not has_token:
                logger.warning("⚠️  DIARIZATION_USE_AUTH_TOKEN이 설정되지 않았습니다!")
                logger.warning("⚠️  모델 다운로드에 실패할 수 있습니다.")
            
            # PyTorch 2.6+ 호환성: pyannote 모델 로드를 위해 weights_only 제한 완화
            # pyannote 라이브러리가 아직 PyTorch 2.6의 새로운 보안 정책을 지원하지 않음
            # Reference: https://pytorch.org/docs/stable/generated/torch.load.html
            import torch
            original_load = torch.load
            def patched_load(*args, **kwargs):
                # pyannote 로드 시 weights_only=False 강제 적용
                kwargs['weights_only'] = False
                return original_load(*args, **kwargs)
            torch.load = patched_load
            
            # HuggingFace 로그인
            if self._settings.DIARIZATION_USE_AUTH_TOKEN:
                logger.info("🔐 HuggingFace 로그인 중...")
                login(token=self._settings.DIARIZATION_USE_AUTH_TOKEN)
                logger.info("✅ HuggingFace 로그인 완료")
            
            # HuggingFace 모델 로드
            # Reference: https://huggingface.co/pyannote/speaker-diarization-3.1
            # Note: pyannote-audio 3.1+ uses 'token' instead of 'use_auth_token'
            logger.info("📥 pyannote 모델 다운로드/로드 중... (처음에는 다운로드 시간 추가 소요)")
            logger.info("⏳ 이 단계에서 시간이 오래 걸릴 수 있습니다. 잠시만 기다려주세요...")
            
            try:
                logger.debug("🔧 Pipeline.from_pretrained() 호출 중...")
                self._model = Pipeline.from_pretrained(
                    "pyannote/speaker-diarization-3.1",
                    token=self._settings.DIARIZATION_USE_AUTH_TOKEN
                )
                logger.debug("✅ Pipeline.from_pretrained() 완료")
            except Exception as load_error:
                logger.error(f"❌ 모델 로드 실패: {type(load_error).__name__}: {load_error}")
                logger.error("💡 해결 방법:")
                logger.error("   1. https://huggingface.co/pyannote/speaker-diarization-3.1 에서 모델 사용 조건 동의")
                logger.error("   2. https://huggingface.co/settings/tokens 에서 토큰 발급")
                logger.error("   3. DIARIZATION_USE_AUTH_TOKEN 환경변수 설정")
                raise
            finally:
                torch.load = original_load
            
            logger.info("✅ pyannote 모델 로드 완료")
            
            # GPU 사용 설정
            if torch.cuda.is_available() and self._settings.DIARIZATION_DEVICE == "cuda":
                logger.info("🚀 pyannote를 GPU 모드로 전송 중...")
                self._model.to(torch.device("cuda"))
                logger.info("✅ GPU 모드 활성화")
            else:
                logger.info("💻 CPU 모드로 실행")
            
            logger.info("🎉 pyannote 화자 분리 파이프라인 준비 완료! (이제 캐시됨)")
            
        except Exception as e:
            import traceback
            logger.error("="*60)
            logger.error("❌ pyannote 로드 실패!")
            logger.error(f"오류 타입: {type(e).__name__}")
            logger.error(f"오류 메시지: {str(e)}")
            logger.error("상세 스택 트레이스:")
            logger.error(traceback.format_exc())
            logger.error("="*60)
            logger.error("")
            logger.error("💡 문제 해결 가이드:")
            logger.error("1. HuggingFace 토큰 설정 확인:")
            logger.error("   - https://huggingface.co/pyannote/speaker-diarization-3.1 접속")
            logger.error("   - 'Agree and access repository' 클릭하여 모델 사용 동의")
            logger.error("   - https://huggingface.co/settings/tokens 에서 토큰 발급")
            logger.error("   - .env 파일 또는 환경변수에 DIARIZATION_USE_AUTH_TOKEN 설정")
            logger.error("")
            logger.error("2. 네트워크 연결 확인:")
            logger.error("   - HuggingFace에 접속 가능한지 확인")
            logger.error("   - 방화벽 설정 확인")
            logger.error("")
            logger.error("3. 의존성 확인:")
            logger.error("   - pip install pyannote.audio torch torchaudio")
            logger.error("   - pip list | grep pyannote")
            logger.error("="*60)
            
            raise RuntimeError(
                f"pyannote 모델 로드 실패: {type(e).__name__}: {str(e)}\n"
                "위의 가이드를 참고하여 문제를 해결하세요."
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