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
            "-y",  # 출력 파일이 이미 있어도 질문 없이 덮어쓴다
            "-i",  # 입력 파일 지정
            video_path,
            "-vn",  # Video 무시 (오디오만 사용하니까)
            "-ac",  # 출력 오디오 채널 수를 1개(모노)로 설정
            "1",
            "-ar",  # 출력 오디오 샘플레이트를 sr(16kHz)로 resample
            str(sr),
            "-f",  # wav로 저장 강제
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
