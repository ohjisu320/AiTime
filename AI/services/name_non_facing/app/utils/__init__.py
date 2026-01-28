# services/name_non_facing/app/utils/__init__.py
"""
유틸리티 모듈

Audio:
    - extract_audio_from_video: 비디오에서 오디오 추출
    - load_audio, load_audio_from_video: 오디오 로드
    - normalize_audio, resample_audio: 오디오 전처리
    
Visualize:
    - 분석 결과 시각화
"""

from app.utils.audio import (
    extract_audio_from_video,
    load_audio,
    load_audio_from_video,
    normalize_audio,
    resample_audio,
    audio_to_float32,
    get_audio_duration,
    extract_segment,
    compute_rms,
    compute_db,
    split_stereo,
    STANDARD_SAMPLE_RATE,
)

__all__ = [
    # Audio
    "extract_audio_from_video",
    "load_audio",
    "load_audio_from_video",
    "normalize_audio",
    "resample_audio",
    "audio_to_float32",
    "get_audio_duration",
    "extract_segment",
    "compute_rms",
    "compute_db",
    "split_stereo",
    "STANDARD_SAMPLE_RATE",
]