import shutil
import subprocess


class FFmpegAudioExtractor:
    @staticmethod
    def extract_wav(video_path: str, wav_path: str, sr: int = 16000) -> None:
        ffmpeg = shutil.which("ffmpeg")
        if ffmpeg is None:
            raise RuntimeError(
                "ffmpeg를 찾을 수 없습니다. (PATH에 ffmpeg가 없음)\n"
                "Windows라면 ffmpeg 설치 후 환경변수 PATH에 추가하거나, "
                "conda-forge의 ffmpeg를 설치하세요: conda install -c conda-forge ffmpeg"
            )

        cmd = [
            ffmpeg,
            "-y",
            "-i",
            video_path,
            "-vn",
            "-ac",
            "1",
            "-ar",
            str(sr),
            "-f",
            "wav",
            wav_path,
        ]
        p = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False,
        )
        if p.returncode != 0:
            raise RuntimeError(f"ffmpeg 실패:\n{p.stderr}")
