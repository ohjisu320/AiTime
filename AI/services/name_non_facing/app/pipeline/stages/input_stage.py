# services/name_non_facing/app/pipeline/stages/input_stage.py
"""
입력 처리 Stage

비디오 파일에서 오디오를 추출하고 로드합니다.

처리 과정 : 
    video.mp4
        ↓ FFmpeg
        ↓ -vn (비디오 제거)
        ↓ -ar 16000 (16kHz 리샘플링)
        ↓ -ac 1 (mono)
        ↓ -acodec pcm_s16le (16-bit PCM)
    temp.wav
        ↓ torchaudio.load()
    np.ndarray (float32, [-1, 1])


설계 의도:
    1. 관심사 분리 (Separation of Concerns)
       - 입력 처리를 독립된 Stage로 분리
       - 다른 Stage는 추출된 audio에만 의존
       
    2. 유연한 입력 지원
       - 비디오 파일 → 오디오 추출
       - (mvp는 아님. 향후 가능.) 오디오 파일 직접 입력 지원
       - (mvp는 아님. 향후 가능.) 실시간 스트림 지원

Reference:
    - FFmpeg: https://ffmpeg.org/ffmpeg.html
    - 오디오 표준: 16kHz, mono, float32 (Whisper/pyannote 요구사항)
"""

from pathlib import Path
from typing import Optional
import logging

from app.pipeline.stages.base_stage import BaseStage 
from app.pipeline.context import PipelineContext 
from app.utils.audio import extract_audio_from_video, load_audio
from app.config import get_settings

logger = logging.getLogger(__name__)


class InputStage(BaseStage):
    """
    입력 처리 Stage
    
    비디오에서 오디오를 추출하고, 분석에 필요한 형식으로 변환합니다.
    
    Input:
        - context.video_path: 비디오 파일 경로
        
    Output:
        - context.audio: 오디오 데이터 (np.ndarray, float32)
        - context.sample_rate: 샘플레이트 (16000)
        - context.audio_duration_sec: 오디오 길이
        - context.audio_path: 추출된 오디오 파일 경로
    """
    
    def __init__(self):
        self._settings = get_settings()
    
    @property
    def name(self) -> str:
        return "InputStage"
    
    def validate(self, context: PipelineContext) -> Optional[str]:
        """비디오 파일 존재 여부 검증"""
        video_path = Path(context.video_path)
        if not video_path.exists():
            return f"비디오 파일이 존재하지 않습니다: {video_path}"
        return None
    
    def process(self, context: PipelineContext) -> PipelineContext:
        """
        비디오에서 오디오 추출 및 로드
        
        Process:
            1. FFmpeg로 비디오 → WAV 변환
            2. torchaudio로 오디오 로드
            3. 표준 형식 검증 (16kHz, mono, float32)
        """
        # 1. 비디오에서 오디오 추출
        audio_path = extract_audio_from_video(
            video_path=context.video_path,
            sample_rate=self._settings.AUDIO_SAMPLE_RATE,
            mono=True
        )
        context.audio_path = str(audio_path)
        
        # 2. 오디오 로드
        audio, sample_rate = load_audio(
            file_path=audio_path,
            sample_rate=self._settings.AUDIO_SAMPLE_RATE,
            mono=True
        )
        
        # 3. 컨텍스트에 저장
        context.audio = audio
        context.sample_rate = sample_rate
        context.audio_duration_sec = len(audio) / sample_rate
        
        logger.info(
            f"🩵🩵🩵 오디오 로드 완료: "
            f"{context.audio_duration_sec:.2f}초, "
            f"{sample_rate}Hz"
        )
        
        return context
