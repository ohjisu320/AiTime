import os

from app.rtn.audio.ffmpeg import FFmpegAudioExtractor
from app.rtn.audio.vad_silero import SileroVAD
from app.rtn.config import VADConfig


def merge_close_segments(
    segs: list[tuple[float, float]],
    gap_s: float,
) -> list[tuple[float, float]]:
    """
    VAD가 반환한 구간들 중 서로 가까운(간격 <= gap_s) 구간을 하나로 병합한다.
    """
    if not segs:
        return []
    segs = sorted(segs, key=lambda x: x[0])
    merged = [segs[0]]
    for s, e in segs[1:]:
        ps, pe = merged[-1]
        if s - pe <= gap_s:
            merged[-1] = (ps, max(pe, e))
        else:
            merged.append((s, e))
    return merged


def vad_segments_from_video(
    video_path: str,
    vad: SileroVAD,
    cfg: VADConfig,
    tmp_dir: str,
) -> list[tuple[float, float]]:
    """
    비디오에서 오디오를 추출(wav)한 뒤 Silero VAD로 발화 구간을 검출하고,
    가까운 구간은 병합한다.

    주의:
    - ffmpeg 추출 실패(오디오 없음/코덱 문제) 시 예외가 발생할 수 있다.
    """
    os.makedirs(tmp_dir, exist_ok=True)

    # wav 파일명은 고정이므로 tmp_dir를 요청 단위로 분리해야 동시성 안전
    # 현재는 TemporaryDirectory로 생성되는 상태
    wav_path = os.path.join(tmp_dir, "audio_16k_mono.wav")

    # VAD 입력을 단순화: 스테레오는 mono로 다운믹스해 채널 차이에 의한 변동 감소
    FFmpegAudioExtractor.extract_wav(video_path, wav_path, sr=cfg.sr)

    segs = vad.segments_from_wav(wav_path)
    return merge_close_segments(segs, gap_s=cfg.merge_gap_s)
