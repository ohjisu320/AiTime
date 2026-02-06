# services/name_non_facing/app/models/speech_recognizer.py
"""
음성 인식 (Speech Recognition) 모듈

faster-whisper를 사용하여 음성을 텍스트로 변환하고,
호명 트리거 탐지 및 아이 발화 분석을 수행합니다.

Reference:
    - Whisper Paper: https://arxiv.org/abs/2212.04356
    - faster-whisper: https://github.com/SYSTRAN/faster-whisper
    - OpenAI Whisper: https://github.com/openai/whisper
    
특징:
    - faster-whisper: 원본 대비 4배 빠른 추론 속도
    - CTranslate2 기반 최적화
    - word-level timestamps 지원

Whisper 선정 이유:

| 특성                 | 설명                                | 출처                                               |
| --------------------| ----------------------------------- | -------------------------------------------------- |
| 노이즈 강인성         | 가정 내 생활 소음에서도 높은 인식률 | [Whisper Paper](https://arxiv.org/abs/2212.04356)  |
| 한국어 성능           | 다국어 학습으로 한국어 우수 지원    | [OpenAI Blog](https://openai.com/research/whisper) |
| 단어 타임스탬프       | word-level timestamps 지원          | [GitHub](https://github.com/openai/whisper)        |
| 다양한 모델 크기      | 하드웨어에 맞게 선택 가능           | -                                                  |

faster-whisper 사용 이유:

| 특성       | 설명                               | 출처                                                        |
| ---------- | ---------------------------------- | ----------------------------------------------------------- |
| 속도        | 원본 대비 4배 이상 빠름            | [faster-whisper](https://github.com/SYSTRAN/faster-whisper) |
| 메모리      | CTranslate2 기반으로 메모리 효율적  | -                                                           |
| 호환성      | 원본 Whisper와 동일 API            | -                                                           |

모델 크기별 특성:

| Model        | Parameters | VRAM  | 상대 속도 | 권장 사용처       |
| ------------ | ---------- | ----- | --------- | ----------------- |
| tiny         | 39M        | ~1GB  | ~32x      | 빠른 테스트       |
| base         | 74M        | ~1GB  | ~16x      | 경량 환경         |
| small        | 244M       | ~2GB  | ~6x       | 균형              |
| medium       | 769M       | ~5GB  | ~2x       | 고품질            |
| large-v3     | 1550M      | ~10GB | 1x        | 프로덕션 권장 |
"""

from dataclasses import dataclass, field
from typing import List
import logging
import re

import numpy as np

from app.config import get_settings
from app.models.base import BaseModel

logger = logging.getLogger(__name__)


@dataclass
class Word:
    """단어 정보"""
    text: str                 # 단어 텍스트
    start_sec: float          # 시작 시점
    end_sec: float            # 종료 시점
    probability: float        # 신뢰도
    
    @property
    def duration_sec(self) -> float:
        return self.end_sec - self.start_sec
    
    def __repr__(self) -> str:
        return f"Word('{self.text}', {self.start_sec:.2f}s~{self.end_sec:.2f}s)"


@dataclass
class Segment:
    """발화 구간 (문장/구 단위)"""
    id: int
    text: str
    start_sec: float
    end_sec: float
    words: List[Word] = field(default_factory=list)
    avg_logprob: float = 0.0
    no_speech_prob: float = 0.0
    
    @property
    def duration_sec(self) -> float:
        return self.end_sec - self.start_sec
    
    def __repr__(self) -> str:
        return f"Segment({self.id}, '{self.text[:30]}...', {self.start_sec:.2f}s~{self.end_sec:.2f}s)"


@dataclass
class TranscriptionResult:
    """음성 인식 결과"""
    text: str                          # 전체 텍스트
    segments: List[Segment]            # 구간별 텍스트
    language: str                      # 감지된 언어
    language_probability: float        # 언어 감지 확률
    duration_sec: float                # 전체 길이
    
    def get_words(self) -> List[Word]:
        """모든 단어 목록 반환"""
        words = []
        for seg in self.segments:
            words.extend(seg.words)
        return words
    
    def get_text_in_range(
        self, 
        start_sec: float, 
        end_sec: float
    ) -> str:
        """특정 시간 범위의 텍스트 반환"""
        words = []
        for word in self.get_words():
            if word.end_sec > start_sec and word.start_sec < end_sec:
                words.append(word.text)
        return "".join(words)


@dataclass
class NameCallEvent:
    """호명 이벤트"""
    text: str                 # 호명 텍스트 ("철수야!" 등)
    start_sec: float          # 호명 시작 시점
    end_sec: float            # 호명 종료 시점 (T_start)
    confidence: float         # 신뢰도
    trial_index: int = 0      # 시도 번호
    
    def __repr__(self) -> str:
        return f"비대면 호명반응('{self.text}', trial={self.trial_index}, end={self.end_sec:.2f}s)"


class SpeechRecognizer(BaseModel):
    """
    faster-whisper 기반 음성 인식기
    
    Usage:
        recognizer = SpeechRecognizer()
        
        # 전체 오디오 인식
        result = recognizer.transcribe(audio, sample_rate=16000)
        print(result.text)
        
        # 호명 탐지
        name_calls = recognizer.find_name_calls(result, "철수")
        for call in name_calls:
            print(f"{call.start_sec:.2f}s: {call.text}")
    
    Reference:
        https://github.com/SYSTRAN/faster-whisper#usage
    """
    
    def __init__(self):
        """초기화"""
        self._settings = get_settings()
    
    def _load_model(self) -> None:
        """
        faster-whisper 모델 로드
        
        Reference: https://github.com/SYSTRAN/faster-whisper#usage
        """
        model_size = self._settings.WHISPER_MODEL_SIZE.value
        logger.info(f"Whisper 모델 로딩: {model_size}")
        
        from faster_whisper import WhisperModel
        
        device = self._settings.WHISPER_DEVICE
        compute_type = self._settings.WHISPER_COMPUTE_TYPE
        
        try:
            self._model = WhisperModel(
                model_size_or_path=model_size,
                device=device,
                compute_type=compute_type,
            )
        except Exception as e:
            # CUDA 라이브러리 문제 시 CPU로 fallback
            if "cublas" in str(e).lower() or "cuda" in str(e).lower():
                logger.warning(f" CUDA 라이브러리 오류, CPU 모드로 전환: {e}")
                device = "cpu"
                compute_type = "int8"
                self._model = WhisperModel(
                    model_size_or_path=model_size,
                    device=device,
                    compute_type=compute_type,
                )
            else:
                raise
        
        logger.info(f"Whisper 모델 로드 완료 ({device})")
    
    def predict(
        self,
        audio: np.ndarray,
        sample_rate: int = None
    ) -> TranscriptionResult:
        """
        음성 인식 수행 (BaseModel 인터페이스)
        """
        return self.transcribe(audio, sample_rate)
    
    def transcribe(
        self,
        audio: np.ndarray,
        sample_rate: int = None,
        language: str = None
    ) -> TranscriptionResult:
        """
        음성 인식 수행
        
        Args:
            audio: 오디오 데이터 (numpy array, mono, float32)
            sample_rate: 샘플레이트 (16000 권장)
            language: 언어 코드 (None이면 설정값 사용)
            
        Returns:
            TranscriptionResult: 인식 결과
            
        Note:
            Whisper는 16kHz 오디오를 기대합니다.
            다른 샘플레이트인 경우 내부적으로 리샘플링됩니다.
        """
        self.ensure_loaded()
        
        if sample_rate is None:
            sample_rate = self._settings.AUDIO_SAMPLE_RATE
        
        if language is None:
            language = self._settings.WHISPER_LANGUAGE
        
        # float32로 변환 및 정규화
        if audio.dtype != np.float32:
            audio = audio.astype(np.float32)
        
        if len(audio) > 0 and np.abs(audio).max() > 1.0:
            audio = audio / np.abs(audio).max()
        
        # faster-whisper 실행
        # Reference: https://github.com/SYSTRAN/faster-whisper#usage
        # CUDA 런타임 에러 발생 시 CPU로 재시도
        try:
            segments_generator, info = self._model.transcribe(
                audio,
                language=language,
                beam_size=self._settings.WHISPER_BEAM_SIZE,
                word_timestamps=self._settings.WHISPER_WORD_TIMESTAMPS,
                vad_filter=True,  # 내장 VAD 필터 사용
            )
        except Exception as e:
            if ("cublas" in str(e).lower() or "cuda" in str(e).lower()) and \
               hasattr(self, "_current_device") and self._current_device != "cpu":
                # CUDA 실행 에러 → CPU 모드로 재로드 및 재시도
                logger.warning(
                    f"⚠️ CUDA 실행 실패 (cublas 라이브러리 누락), CPU로 재시도: {e}"
                )
                from faster_whisper import WhisperModel
                model_size = self._settings.WHISPER_MODEL_SIZE.value
                self._current_device = "cpu"
                self._current_compute_type = "int8"
                self._model = WhisperModel(
                    model_size_or_path=model_size,
                    device="cpu",
                    compute_type="int8",
                )
                logger.info("✅ CPU 모드로 모델 재로드 완료, 재시도 중...")
                
                # CPU로 재시도
                segments_generator, info = self._model.transcribe(
                    audio,
                    language=language,
                    beam_size=self._settings.WHISPER_BEAM_SIZE,
                    word_timestamps=self._settings.WHISPER_WORD_TIMESTAMPS,
                    vad_filter=True,
                )
            else:
                raise
        
        # 결과 파싱
        # Generator iteration 중에도 CUDA 에러 발생 가능하므로 try-catch
        segments = []
        full_text_parts = []
        
        try:
            for seg in segments_generator:
                words = []
                if seg.words:
                    for w in seg.words:
                        word = Word(
                            text=w.word,
                            start_sec=w.start,
                            end_sec=w.end,
                            probability=w.probability
                        )
                        words.append(word)
                
                segment = Segment(
                    id=seg.id,
                    text=seg.text.strip(),
                    start_sec=seg.start,
                    end_sec=seg.end,
                    words=words,
                    avg_logprob=seg.avg_logprob,
                    no_speech_prob=seg.no_speech_prob
                )
                segments.append(segment)
                full_text_parts.append(seg.text.strip())
        except Exception as e:
            if ("cublas" in str(e).lower() or "cuda" in str(e).lower()) and \
               hasattr(self, "_current_device") and self._current_device != "cpu":
                # Generator iteration 중 CUDA 에러 → CPU로 재시도
                logger.warning(
                    f"⚠️ CUDA 실행 실패 (generator iteration 중 cublas 누락), CPU로 전체 재시도: {e}"
                )
                from faster_whisper import WhisperModel
                model_size = self._settings.WHISPER_MODEL_SIZE.value
                self._current_device = "cpu"
                self._current_compute_type = "int8"
                self._model = WhisperModel(
                    model_size_or_path=model_size,
                    device="cpu",
                    compute_type="int8",
                )
                logger.info("✅ CPU 모드로 모델 재로드 완료, 재시도 중...")
                
                # CPU로 전체 재시도
                segments_generator, info = self._model.transcribe(
                    audio,
                    language=language,
                    beam_size=self._settings.WHISPER_BEAM_SIZE,
                    word_timestamps=self._settings.WHISPER_WORD_TIMESTAMPS,
                    vad_filter=True,
                )
                
                # 결과 파싱 재시도
                segments = []
                full_text_parts = []
                for seg in segments_generator:
                    words = []
                    if seg.words:
                        for w in seg.words:
                            word = Word(
                                text=w.word,
                                start_sec=w.start,
                                end_sec=w.end,
                                probability=w.probability
                            )
                            words.append(word)
                    
                    segment = Segment(
                        id=seg.id,
                        text=seg.text.strip(),
                        start_sec=seg.start,
                        end_sec=seg.end,
                        words=words,
                        avg_logprob=seg.avg_logprob,
                        no_speech_prob=seg.no_speech_prob
                    )
                    segments.append(segment)
                    full_text_parts.append(seg.text.strip())
            else:
                raise
        
        result = TranscriptionResult(
            text=" ".join(full_text_parts),
            segments=segments,
            language=info.language,
            language_probability=info.language_probability,
            duration_sec=info.duration
        )
        
        logger.debug(
            f"💛 음성 인식 완료: {len(segments)}개 구간, "
            f"{result.duration_sec:.2f}초"
        )
        
        return result
    
    def transcribe_segment(
        self,
        audio: np.ndarray,
        start_sec: float,
        end_sec: float,
        sample_rate: int = None
    ) -> TranscriptionResult:
        """
        특정 구간만 인식
        
        Args:
            audio: 전체 오디오
            start_sec: 시작 시점
            end_sec: 종료 시점
            sample_rate: 샘플레이트
            
        Returns:
            TranscriptionResult: 해당 구간 인식 결과
        """
        if sample_rate is None:
            sample_rate = self._settings.AUDIO_SAMPLE_RATE
        
        start_sample = int(start_sec * sample_rate)
        end_sample = int(end_sec * sample_rate)
        
        segment_audio = audio[start_sample:end_sample]
        result = self.transcribe(segment_audio, sample_rate)
        
        # 타임스탬프를 절대 시간으로 조정
        for seg in result.segments:
            seg.start_sec += start_sec
            seg.end_sec += start_sec
            for word in seg.words:
                word.start_sec += start_sec
                word.end_sec += start_sec
        
        return result
    
    def find_name_calls(
        self,
        transcription: TranscriptionResult,
        child_name: str,
        child_nickname: str = None
    ) -> List[NameCallEvent]:
        """
        호명 이벤트 탐지
        # TODO 호명 이벤트 탐지 로직이 아직 미흡함
        
        호명 패턴 (한국어):
        - "{이름}아", "{이름}야" (호격 조사)
        - "우리 {이름}", "우리 {이름}이"
        - "{이름}아, 여기 봐", "{이름}아!" 등
        
        Args:
            transcription: 음성 인식 결과
            child_name: 아이 이름
            child_nickname: 아이 애칭 (선택)
            
        Returns:
            List[NameCallEvent]: 호명 이벤트 목록 (시간순)
        """
        name_calls = []
        words = transcription.get_words()
        
        if not words:
            # 단어 타임스탬프가 없는 경우 segment 기반 탐지
            return self._find_name_calls_by_segments(
                transcription, child_name, child_nickname
            )
        
        # 탐지할 이름 목록
        names_to_find = [child_name]
        if child_nickname:
            names_to_find.append(child_nickname)
        
        # 호명 패턴 정규식
        # Reference: 한국어 호격 조사 패턴
        patterns = []
        for name in names_to_find:
            patterns.extend([
                rf"{name}[아야]",           # 철수야, 철수아
                rf"우리\s*{name}",          # 우리 철수
                rf"{name}[이]?[!?]",        # 철수! 철수이!
                rf"{name}\s*여기",          # 철수 여기
                name,                        # 이름만
            ])
        
        combined_pattern = "|".join(patterns)
        
        # 연속된 단어들을 검사
        i = 0
        trial_index = 1
        
        while i < len(words):
            # 현재 위치에서 최대 5개 단어를 조합하여 검사
            for window_size in range(1, min(6, len(words) - i + 1)):
                window_words = words[i:i + window_size]
                window_text = "".join(w.text for w in window_words)
                
                # 정규식 매칭
                if re.search(combined_pattern, window_text, re.IGNORECASE):
                    # 호명 이벤트 생성
                    event = NameCallEvent(
                        text=window_text.strip(),
                        start_sec=window_words[0].start_sec,
                        end_sec=window_words[-1].end_sec,
                        confidence=np.mean([w.probability for w in window_words]),
                        trial_index=trial_index
                    )
                    name_calls.append(event)
                    trial_index += 1
                    i += window_size
                    break
            else:
                i += 1
        
        logger.info(f"호명 탐지 완료: {len(name_calls)}개 호명 이벤트")
        return name_calls
    
    def _find_name_calls_by_segments(
        self,
        transcription: TranscriptionResult,
        child_name: str,
        child_nickname: str = None
    ) -> List[NameCallEvent]:
        """
        Segment 기반 호명 탐지 (word timestamps 없는 경우)
        """
        name_calls = []
        names_to_find = [child_name]
        if child_nickname:
            names_to_find.append(child_nickname)
        
        patterns = []
        for name in names_to_find:
            patterns.extend([
                rf"{name}[아야]",
                rf"우리\s*{name}",
                rf"{name}[이]?[!?]",
                name,
            ])
        
        combined_pattern = "|".join(patterns)
        trial_index = 1
        
        for seg in transcription.segments:
            matches = list(re.finditer(combined_pattern, seg.text, re.IGNORECASE))
            for match in matches:
                # 구간 내 상대적 위치로 시간 추정
                text_len = len(seg.text) if len(seg.text) > 0 else 1
                rel_start = match.start() / text_len
                rel_end = match.end() / text_len
                
                duration = seg.end_sec - seg.start_sec
                start_sec = seg.start_sec + (duration * rel_start)
                end_sec = seg.start_sec + (duration * rel_end)
                
                event = NameCallEvent(
                    text=match.group(),
                    start_sec=start_sec,
                    end_sec=end_sec,
                    confidence=1.0 - seg.no_speech_prob,
                    trial_index=trial_index
                )
                name_calls.append(event)
                trial_index += 1
        
        return name_calls
    
    def is_name_call(
        self,
        text: str,
        child_name: str,
        child_nickname: str = None
    ) -> bool:
        """
        텍스트가 호명인지 판단
        
        Args:
            text: 검사할 텍스트
            child_name: 아이 이름
            child_nickname: 아이 애칭
            
        Returns:
            bool: 호명 여부
        """
        names = [child_name]
        if child_nickname:
            names.append(child_nickname)
        
        for name in names:
            patterns = [
                rf"{name}[아야]",
                rf"우리\s*{name}",
                rf"{name}[이]?[!?]",
            ]
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    return True
        
        return False