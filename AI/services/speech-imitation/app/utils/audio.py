"""
오디오 유틸리티 모듈

- FFmpeg로 비디오에서 오디오 추출
- torchaudio/librosa로 로드
- 구간 슬라이스/저장 등 후속 처리 지원
"""

import contextlib
import logging
import subprocess
import tempfile
from pathlib import Path

import numpy as np

logger = logging.getLogger(__name__)

STANDARD_SAMPLE_RATE = 16000


def extract_audio_from_video(
    video_path: str | Path,
    output_path: str | Path | None = None,
    sample_rate: int = STANDARD_SAMPLE_RATE,
    mono: bool = True,
) -> Path:
    """
    FFmpeg로 비디오에서 오디오(wav, pcm_s16le) 추출
    """
    video_path = Path(video_path)
    if not video_path.exists():
        raise FileNotFoundError(f"비디오 파일이 존재하지 않습니다: {video_path}")

    if output_path is None:
        output_path = Path(tempfile.mktemp(suffix=".wav"))
    else:
        output_path = Path(output_path)

    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        str(video_path),
        "-vn",
        "-acodec",
        "pcm_s16le",
        "-ar",
        str(sample_rate),
    ]
    if mono:
        cmd.extend(["-ac", "1"])
    cmd.append(str(output_path))

    logger.info(f"⭕ FFmpeg 오디오 추출: {video_path} -> {output_path}")
    try:
        subprocess.run(cmd, capture_output=True, text=True, check=True)
    except FileNotFoundError as e:
        raise RuntimeError(
            "FFmpeg가 설치되어 있지 않습니다. "
            "apt install ffmpeg 또는 brew install ffmpeg로 설치하세요."
        ) from e
    except subprocess.CalledProcessError as e:
        logger.error(f"✖️ FFmpeg 오류: {e.stderr}")
        raise RuntimeError(f"오디오 추출 실패: {e.stderr}") from e

    return output_path


def load_audio(
    file_path: str | Path,
    sample_rate: int | None = None,
    mono: bool = True,
) -> tuple[np.ndarray, int]:
    """
    오디오 파일 로드
    - torchaudio 우선
    - 실패 시 librosa fallback
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"오디오 파일이 존재하지 않습니다: {file_path}")

    try:
        import torchaudio  # type: ignore

        waveform, sr = torchaudio.load(str(file_path))
        if mono and waveform.shape[0] > 1:
            waveform = waveform.mean(dim=0, keepdim=True)

        if sample_rate is not None and sr != sample_rate:
            resampler = torchaudio.transforms.Resample(sr, sample_rate)
            waveform = resampler(waveform)
            sr = sample_rate

        audio = waveform.squeeze().numpy().astype(np.float32)

    except ImportError:
        logger.warning("torchaudio 미설치, librosa 사용")
        import librosa  # type: ignore

        audio, sr = librosa.load(str(file_path), sr=sample_rate, mono=mono)
        audio = audio.astype(np.float32)

    return audio, int(sr)


def load_audio_from_video(
    video_path: str | Path,
    sample_rate: int = STANDARD_SAMPLE_RATE,
    mono: bool = True,
    keep_audio_file: bool = False,
) -> tuple[np.ndarray, int, Path | None]:
    """
    비디오에서 오디오 추출 후 로드
    Returns:
        (audio, sr, wav_path_if_kept)
    """
    wav_path = extract_audio_from_video(video_path, sample_rate=sample_rate, mono=mono)
    audio, sr = load_audio(wav_path, sample_rate=sample_rate, mono=mono)

    kept = wav_path if keep_audio_file else None
    if not keep_audio_file:
        with contextlib.suppress(Exception):
            wav_path.unlink(missing_ok=True)

    return audio, sr, kept


def slice_audio(
    audio: np.ndarray,
    sample_rate: int,
    start_sec: float,
    end_sec: float,
) -> np.ndarray:
    """
    오디오 구간 슬라이스 (초 단위)
    """
    s = max(0, int(start_sec * sample_rate))
    e = min(len(audio), int(end_sec * sample_rate))
    if e <= s:
        return np.zeros((0,), dtype=np.float32)
    return audio[s:e]


def save_wav(
    path: str | Path,
    audio: np.ndarray,
    sample_rate: int,
) -> Path:
    """
    float32 [-1,1] mono 오디오를 wav로 저장
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    # 안전하게 int16로 저장
    x = np.clip(audio, -1.0, 1.0)
    x16 = (x * 32767.0).astype(np.int16)

    try:
        import soundfile as sf  # type: ignore

        sf.write(str(path), x, sample_rate, subtype="PCM_16")
    except Exception:
        # 표준 라이브러리 fallback
        import wave

        with wave.open(str(path), "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            wf.writeframes(x16.tobytes())

    return path
