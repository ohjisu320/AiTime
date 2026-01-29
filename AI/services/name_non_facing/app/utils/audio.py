# services/name_non_facing/app/utils/audio.py
"""
오디오 유틸리티 모듈

비디오에서 오디오 추출, 리샘플링, 정규화 등
오디오 전처리 기능을 제공합니다.

참고:
    - FFmpeg: https://ffmpeg.org/documentation.html
    - torchaudio: https://pytorch.org/audio/stable/
    - librosa: https://librosa.org/doc/latest/
"""

import logging
import subprocess
import tempfile
from pathlib import Path
from typing import Tuple, Union

import numpy as np

logger = logging.getLogger(__name__)

# 표준 샘플레이트 (Whisper, pyannote 등 대부분 모델의 요구사항)
STANDARD_SAMPLE_RATE = 16000


def extract_audio_from_video(
    video_path: Union[str, Path],
    output_path: Union[str, Path] = None,
    sample_rate: int = STANDARD_SAMPLE_RATE,
    mono: bool = True
) -> Path:
    """
    FFmpeg를 사용하여 비디오에서 오디오 추출
    
    Args:
        video_path: 입력 비디오 파일 경로
        output_path: 출력 오디오 파일 경로 (None이면 임시 파일)
        sample_rate: 출력 샘플레이트 (기본: 16000)
        mono: 모노 변환 여부 (기본: True)
        
    Returns:
        Path: 추출된 오디오 파일 경로
        
    Raises:
        FileNotFoundError: 비디오 파일이 존재하지 않는 경우
        RuntimeError: FFmpeg 실행 오류
        
    Example:
        >>> audio_path = extract_audio_from_video("video.mp4")
        >>> audio, sr = load_audio(audio_path)
    """
    video_path = Path(video_path)
    
    if not video_path.exists():
        raise FileNotFoundError(f"비디오 파일이 존재하지 않습니다: {video_path}")
    
    if output_path is None:
        # 임시 파일 생성
        output_path = Path(tempfile.mktemp(suffix=".wav"))
    else:
        output_path = Path(output_path)
    
    # FFmpeg 명령 구성
    cmd = [
        "ffmpeg",
        "-y",                       # 덮어쓰기 허용
        "-i", str(video_path),      # 입력 파일
        "-vn",                      # 비디오 스트림 제거
        "-acodec", "pcm_s16le",     # 16-bit PCM
        "-ar", str(sample_rate),    # 샘플레이트
    ]
    
    if mono:
        cmd.extend(["-ac", "1"])    # 모노 채널
    
    cmd.append(str(output_path))
    
    logger.info(f"⭕ FFmpeg 오디오 추출: {video_path} -> {output_path}")
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )
    except subprocess.CalledProcessError as e:
        logger.error(f"✖️ FFmpeg 오류: {e.stderr}")
        raise RuntimeError(f"✖️ 오디오 추출 실패: {e.stderr}")
    except FileNotFoundError:
        raise RuntimeError(
            "FFmpeg가 설치되어 있지 않습니다. "
            "apt install ffmpeg 또는 brew install ffmpeg로 설치하세요."
        )
    
    logger.info(f"⭕ 오디오 추출 완료: {output_path}")
    return output_path


def load_audio(
    file_path: Union[str, Path],
    sample_rate: int = None,
    mono: bool = True
) -> Tuple[np.ndarray, int]:
    """
    오디오 파일 로드
    
    torchaudio 우선 사용, 실패 시 librosa fallback
    
    Args:
        file_path: 오디오 파일 경로
        sample_rate: 원하는 샘플레이트 (None이면 원본 유지)
        mono: 모노 변환 여부
        
    Returns:
        Tuple[np.ndarray, int]: (오디오 데이터, 샘플레이트)
            - 오디오: float32, [-1.0, 1.0] 정규화, shape=(samples,)
    """
    file_path = Path(file_path)
    
    if not file_path.exists():
        raise FileNotFoundError(f"✖️ 오디오 파일이 존재하지 않습니다: {file_path}")
    
    try:
        # torchaudio 사용 (더 빠름)
        import torchaudio
        
        waveform, sr = torchaudio.load(str(file_path))
        
        # 모노 변환
        if mono and waveform.shape[0] > 1:
            waveform = waveform.mean(dim=0, keepdim=True)
        
        # 리샘플링
        if sample_rate is not None and sr != sample_rate:
            resampler = torchaudio.transforms.Resample(sr, sample_rate)
            waveform = resampler(waveform)
            sr = sample_rate
        
        audio = waveform.squeeze().numpy()
        
    except ImportError:
        logger.warning("torchaudio 미설치, librosa 사용")
        import librosa
        
        audio, sr = librosa.load(
            str(file_path),
            sr=sample_rate,
            mono=mono
        )
    
    return audio.astype(np.float32), sr


def load_audio_from_video(
    video_path: Union[str, Path],
    sample_rate: int = STANDARD_SAMPLE_RATE,
    mono: bool = True,
    keep_audio_file: bool = False
) -> Tuple[np.ndarray, int]:
    """
    비디오 파일에서 오디오를 추출하고 로드
    
    내부적으로 FFmpeg를 사용하여 임시 오디오 파일을 생성한 후 로드합니다.
    
    Args:
        video_path: 비디오 파일 경로
        sample_rate: 원하는 샘플레이트
        mono: 모노 변환 여부
        keep_audio_file: 임시 오디오 파일 유지 여부
        
    Returns:
        Tuple[np.ndarray, int]: (오디오 데이터, 샘플레이트)
        
    Example:
        >>> audio, sr = load_audio_from_video("test.mp4")
        >>> print(f"Duration: {len(audio) / sr:.2f}s")
    """
    audio_path = extract_audio_from_video(
        video_path=video_path,
        sample_rate=sample_rate,
        mono=mono
    )
    
    try:
        audio, sr = load_audio(audio_path, sample_rate=sample_rate, mono=mono)
    finally:
        if not keep_audio_file and audio_path.exists():
            audio_path.unlink()
            logger.debug(f"임시 오디오 파일 삭제: {audio_path}")
    
    return audio, sr


def normalize_audio(
    audio: np.ndarray,
    target_db: float = -20.0
) -> np.ndarray:
    """
    오디오 볼륨 정규화 (Peak Normalization)
    
    Args:
        audio: 입력 오디오 (float32)
        target_db: 목표 데시벨 (기본: -20 dB)
        
    Returns:
        np.ndarray: 정규화된 오디오
    """
    # 현재 피크 레벨 계산
    peak = np.abs(audio).max()
    
    if peak == 0:
        logger.warning("무음 오디오, 정규화 스킵")
        return audio
    
    # 목표 레벨 (dB → 선형)
    target_amplitude = 10 ** (target_db / 20)
    
    # 스케일링
    scale = target_amplitude / peak
    normalized = audio * scale
    
    # 클리핑 방지
    normalized = np.clip(normalized, -1.0, 1.0)
    
    return normalized.astype(np.float32)


def resample_audio(
    audio: np.ndarray,
    orig_sr: int,
    target_sr: int
) -> np.ndarray:
    """
    오디오 리샘플링
    
    Args:
        audio: 입력 오디오
        orig_sr: 원본 샘플레이트
        target_sr: 목표 샘플레이트
        
    Returns:
        np.ndarray: 리샘플링된 오디오
    """
    if orig_sr == target_sr:
        return audio
    
    try:
        import torchaudio
        import torch
        
        waveform = torch.from_numpy(audio).unsqueeze(0)
        resampler = torchaudio.transforms.Resample(orig_sr, target_sr)
        resampled = resampler(waveform).squeeze().numpy()
        
    except ImportError:
        import librosa
        resampled = librosa.resample(audio, orig_sr=orig_sr, target_sr=target_sr)
    
    return resampled.astype(np.float32)


def audio_to_float32(audio: np.ndarray) -> np.ndarray:
    """
    오디오를 float32 형식으로 변환
    
    int16 (-32768 ~ 32767) → float32 (-1.0 ~ 1.0)
    
    Args:
        audio: 입력 오디오 (int16 또는 float)
        
    Returns:
        np.ndarray: float32 정규화된 오디오
    """
    if audio.dtype == np.float32:
        return audio
    
    if audio.dtype == np.float64:
        return audio.astype(np.float32)
    
    if audio.dtype == np.int16:
        return (audio / 32768.0).astype(np.float32)
    
    if audio.dtype == np.int32:
        return (audio / 2147483648.0).astype(np.float32)
    
    # 기타 타입은 그대로 변환 시도
    logger.warning(f"알 수 없는 오디오 dtype: {audio.dtype}")
    return audio.astype(np.float32)


def get_audio_duration(
    audio: np.ndarray,
    sample_rate: int
) -> float:
    """
    오디오 길이(초) 계산
    
    Args:
        audio: 오디오 데이터
        sample_rate: 샘플레이트
        
    Returns:
        float: 오디오 길이 (초)
    """
    return len(audio) / sample_rate


def extract_segment(
    audio: np.ndarray,
    start_sec: float,
    end_sec: float,
    sample_rate: int
) -> np.ndarray:
    """
    오디오에서 특정 구간 추출
    
    Args:
        audio: 전체 오디오
        start_sec: 시작 시간 (초)
        end_sec: 종료 시간 (초)
        sample_rate: 샘플레이트
        
    Returns:
        np.ndarray: 추출된 오디오 세그먼트
    """
    start_sample = int(start_sec * sample_rate)
    end_sample = int(end_sec * sample_rate)
    
    # 범위 클리핑
    start_sample = max(0, start_sample)
    end_sample = min(len(audio), end_sample)
    
    return audio[start_sample:end_sample]


def compute_rms(audio: np.ndarray) -> float:
    """
    RMS (Root Mean Square) 에너지 계산
    
    Args:
        audio: 오디오 데이터
        
    Returns:
        float: RMS 값
    """
    return float(np.sqrt(np.mean(audio ** 2)))


def compute_db(audio: np.ndarray, ref: float = 1.0) -> float:
    """
    데시벨 레벨 계산
    
    Args:
        audio: 오디오 데이터
        ref: 기준값 (기본: 1.0)
        
    Returns:
        float: dB 값
    """
    rms = compute_rms(audio)
    if rms == 0:
        return -np.inf
    return 20 * np.log10(rms / ref)


def split_stereo(audio: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """
    스테레오 오디오를 좌/우 채널로 분리
    
    Args:
        audio: 스테레오 오디오 (shape: (2, samples) 또는 (samples, 2))
        
    Returns:
        Tuple[np.ndarray, np.ndarray]: (왼쪽 채널, 오른쪽 채널)
    """
    if audio.ndim == 1:
        # 이미 모노
        return audio, audio
    
    if audio.shape[0] == 2:
        return audio[0], audio[1]
    elif audio.shape[1] == 2:
        return audio[:, 0], audio[:, 1]
    else:
        raise ValueError(f"예상치 못한 오디오 shape: {audio.shape}")
