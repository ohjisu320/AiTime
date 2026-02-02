# services/name_non_facing/app/models/vad.py
"""
Silero VAD (Voice Activity Detection) 래퍼 모듈

음성 활동 구간을 탐지하여 무음 구간을 제거하고,
후속 처리(화자 분리, 음성 인식)의 효율을 높입니다.

Reference:
    - GitHub: https://github.com/snakers4/silero-vad
    - Paper: https://arxiv.org/abs/2106.04624
    
특징:
    - 30ms 청크 단위 처리 (초저지연)
    - ~1MB 경량 모델
    - CPU/GPU 모두 지원

Silero VAD 선정 이유:

| 특성             | 설명                                      | 출처                                                         |
| ---------------- | ----------------------------------------- | ------------------------------------------------------------ |
| 초저지연     | 30ms 청크 단위 처리, 실시간 스트리밍 지원 | [Silero VAD GitHub](https://github.com/snakers4/silero-vad)  |
| 경량성       | ~1MB 모델, CPU에서도 빠른 추론            | [Silero VAD Paper](https://arxiv.org/abs/2106.04624)         |
| 정확도       | 다양한 노이즈 환경에서 높은 정확도        | [Benchmark](https://github.com/snakers4/silero-vad#performance) |
| PyTorch 기반 | GPU 가속 지원, 간편한 통합                | -                                                            |

핵심 파라미터 설명:

| 파라미터                  | 기본값 | 설명                            |
| ------------------------- | ------ | ------------------------------- |
| `threshold`               | 0.5    | 음성 확률 임계값. 높을수록 엄격 |
| `min_speech_duration_ms`  | 250    | 이보다 짧은 음성은 무시         |
| `min_silence_duration_ms` | 100    | 음성 내 허용 무음 길이          |
| `speech_pad_ms`           | 30     | 음성 구간 전후 패딩             |
"""

from dataclasses import dataclass
from typing import List, Tuple, Any
import logging

import numpy as np
import torch

from app.config import get_settings
from app.models.base import BaseModel

logger = logging.getLogger(__name__)


@dataclass
class SpeechSegment:
    """음성 구간 정보"""
    start_sec: float          # 시작 시점 (초)
    end_sec: float            # 종료 시점 (초)
    start_sample: int         # 시작 샘플 인덱스
    end_sample: int           # 종료 샘플 인덱스
    confidence: float = 1.0   # 평균 신뢰도 (0~1)
    
    @property
    def duration_sec(self) -> float:
        """구간 길이 (초)"""
        return self.end_sec - self.start_sec
    
    def __repr__(self) -> str: #  디버깅용. 예쁘게.
        return (
            f"SpeechSegment({self.start_sec:.2f}s ~ {self.end_sec:.2f}s, "
            f"duration={self.duration_sec:.2f}s)"
        )


class VoiceActivityDetector(BaseModel):
    """
    Silero VAD 래퍼 클래스
    
    싱글톤 패턴으로 구현되어 모델이 한 번만 로드됩니다.
    
    Usage:
        vad = VoiceActivityDetector()
        segments = vad.detect(audio_data, sample_rate=16000)
        
        for seg in segments:
            print(f"{seg.start_sec:.2f}s ~ {seg.end_sec:.2f}s")
    
    Reference:
        https://github.com/snakers4/silero-vad#usage
    """
    
    _get_speech_timestamps: Any = None
    _utils: Any = None
    
    def __init__(self):
        """초기화"""
        self._settings = get_settings()
    
    def _load_model(self) -> None:
        """
        Silero VAD 모델 로드
        
        PyTorch Hub에서 사전 학습된 모델을 다운로드합니다.
        Reference: https://github.com/snakers4/silero-vad#silero-vad
        """
        logger.info("Silero VAD 모델 로딩...")
        
        # PyTorch Hub에서 모델 로드
        model, utils = torch.hub.load(
            repo_or_dir='snakers4/silero-vad',
            model='silero_vad',
            force_reload=False,
            onnx=False,
            trust_repo=True
        )
        
        self._model = model
        self._utils = utils
        
        # 유틸리티 함수 추출
        (
            self._get_speech_timestamps,
            _,  # save_audio
            _,  # read_audio
            _,  # VADIterator
            _   # collect_chunks
        ) = utils
        
        logger.info("Silero VAD 모델 로드 완료")
    
    def predict(
        self,
        audio: np.ndarray,
        sample_rate: int = None
    ) -> List[SpeechSegment]:
        """
        음성 활동 구간 탐지 (BaseModel 인터페이스)
        
        Args:
            audio: 오디오 데이터 (numpy array, mono)
            sample_rate: 샘플레이트 (기본값: 설정값 사용)
            
        Returns:
            List[SpeechSegment]: 탐지된 음성 구간 목록
        """
        return self.detect(audio, sample_rate)
    
    def detect(
        self,
        audio: np.ndarray,
        sample_rate: int = None,
    ) -> List[SpeechSegment]:
        """
        음성 활동 구간 탐지
        
        Args:
            audio: 오디오 데이터 (numpy array, mono)
            sample_rate: 샘플레이트 (기본값: 설정값 사용)
            
        Returns:
            List[SpeechSegment]: 탐지된 음성 구간 목록
            
        Example:
            >>> vad = VoiceActivityDetector()
            >>> audio, sr = librosa.load("audio.wav", sr=16000)
            >>> segments = vad.detect(audio, sr)
            >>> print(f"발화 구간 수: {len(segments)}")
        """
        self.ensure_loaded()
        
        if sample_rate is None:
            sample_rate = self._settings.AUDIO_SAMPLE_RATE
        
        # numpy to torch tensor
        if isinstance(audio, np.ndarray):
            audio_tensor = torch.from_numpy(audio).float()
        else:
            audio_tensor = audio
        
        # 1D로 변환 (mono)
        if audio_tensor.dim() > 1:
            audio_tensor = audio_tensor.mean(dim=0)
        
        # Silero VAD 실행
        # Reference: https://github.com/snakers4/silero-vad#get_speech_timestamps
        speech_timestamps = self._get_speech_timestamps(
            audio_tensor,
            self._model,
            sampling_rate=sample_rate,
            threshold=self._settings.VAD_THRESHOLD,
            min_speech_duration_ms=self._settings.VAD_MIN_SPEECH_DURATION_MS,
            min_silence_duration_ms=self._settings.VAD_MIN_SILENCE_DURATION_MS,
            window_size_samples=self._settings.VAD_WINDOW_SIZE_SAMPLES,
            speech_pad_ms=self._settings.VAD_SPEECH_PAD_MS,
            return_seconds=False,  # 샘플 단위로 받아서 직접 변환
        )
        
        # SpeechSegment 객체로 변환
        segments = []
        for ts in speech_timestamps:
            start_sample = ts['start']
            end_sample = ts['end']
            
            segment = SpeechSegment(
                start_sec=start_sample / sample_rate,
                end_sec=end_sample / sample_rate,
                start_sample=start_sample,
                end_sample=end_sample,
                confidence=ts.get('confidence', 1.0)
            )
            segments.append(segment)
        
        logger.debug(f"😽 VAD 탐지 완료: {len(segments)}개 음성 구간")
        return segments
    
    def extract_speech(
        self,
        audio: np.ndarray,
        sample_rate: int = None,
        segments: List[SpeechSegment] = None
    ) -> Tuple[np.ndarray, List[SpeechSegment]]:
        """
        음성 구간만 추출하여 연결
        
        Args:
            audio: 원본 오디오
            sample_rate: 샘플레이트
            segments: 미리 탐지된 구간 (없으면 자동 탐지)
            
        Returns:
            Tuple[np.ndarray, List[SpeechSegment]]: 
                (연결된 음성 오디오, 원본 기준 구간 정보)
        """
        if sample_rate is None:
            sample_rate = self._settings.AUDIO_SAMPLE_RATE
            
        if segments is None:
            segments = self.detect(audio, sample_rate)
        
        if not segments:
            return np.array([], dtype=np.float32), []
        
        # 각 구간의 오디오 추출
        speech_chunks = []
        for seg in segments:
            chunk = audio[seg.start_sample:seg.end_sample]
            speech_chunks.append(chunk)
        
        # 연결
        speech_audio = np.concatenate(speech_chunks)
        
        logger.debug(
            f"음성 추출: {len(audio)/sample_rate:.2f}s → "
            f"{len(speech_audio)/sample_rate:.2f}s "
            f"({len(segments)} segments)"
        )
        
        return speech_audio, segments
    
    def detect_in_range(
        self,
        audio: np.ndarray,
        start_sec: float,
        end_sec: float,
        sample_rate: int = None
    ) -> List[SpeechSegment]:
        """
        특정 시간 범위 내 음성 활동 탐지
        
        호명 종료 후 ~ 반응 대기 시간 내 음성 탐지에 활용
        
        Args:
            audio: 전체 오디오
            start_sec: 분석 시작 시점 (초)
            end_sec: 분석 종료 시점 (초)
            sample_rate: 샘플레이트
            
        Returns:
            List[SpeechSegment]: 해당 범위 내 음성 구간 (절대 시간 기준)
        """
        if sample_rate is None:
            sample_rate = self._settings.AUDIO_SAMPLE_RATE
        
        # 범위 검증
        audio_duration = len(audio) / sample_rate
        start_sec = max(0, start_sec)
        end_sec = min(end_sec, audio_duration)
        
        if start_sec >= end_sec:
            return []
        
        start_sample = int(start_sec * sample_rate)
        end_sample = int(end_sec * sample_rate)
        
        # 범위 추출
        audio_chunk = audio[start_sample:end_sample]
        
        if len(audio_chunk) == 0:
            return []
        
        # 해당 범위에서 VAD 실행
        segments = self.detect(audio_chunk, sample_rate)
        
        # 절대 시간으로 변환
        adjusted_segments = []
        for seg in segments:
            adjusted = SpeechSegment(
                start_sec=seg.start_sec + start_sec,
                end_sec=seg.end_sec + start_sec,
                start_sample=seg.start_sample + start_sample,
                end_sample=seg.end_sample + start_sample,
                confidence=seg.confidence
            )
            adjusted_segments.append(adjusted)
        
        return adjusted_segments
    
    def reset_state(self) -> None:
        """
        스트리밍 처리 시 상태 초기화
        
        Reference: https://github.com/snakers4/silero-vad#reset-states
        """
        if self._model is not None:
            self._model.reset_states()
            logger.debug("😺 VAD 상태 초기화")