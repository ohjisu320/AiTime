# AI/services/pose-estimation/app/pipeline/video_processor.py
"""
영상 프레임 추출 모듈.

영상 파일을 입력받아 지정된 FPS로 프레임을 추출합니다.
Generator 패턴을 사용하여 메모리 효율적으로 처리합니다.
"""

import cv2
import logging
from PIL import Image
from pathlib import Path
from typing import Generator, Optional, Any
from dataclasses import dataclass

from app.config import settings
from app.pipeline.exceptions import VideoProcessingError

logger = logging.getLogger(__name__)


@dataclass
class VideoInfo:
    """
    영상 메타데이터.
    
    Attributes:
        path: 파일 경로
        filename: 파일명
        fps: 초당 프레임 수
        width: 영상 너비 (픽셀)
        height: 영상 높이 (픽셀)
        total_frames: 총 프레임 수
        duration_sec: 영상 길이 (초)
        codec: 코덱 정보
    """
    path: str
    filename: str
    fps: float
    width: int
    height: int
    total_frames: int
    duration_sec: float
    codec: str


@dataclass
class FrameExtractionResult:
    """
    프레임 추출 결과 메타데이터.
    
    Attributes:
        output_folder: 저장 폴더 경로
        video_info: 원본 영상 정보
        saved_count: 저장된 프레임 수
        frame_interval: 추출 간격
        file_pattern: 파일명 패턴 (예: "frame_{:05d}.jpg")
        frame_files: 저장된 파일 목록
    """
    output_folder: str
    video_info: VideoInfo
    saved_count: int
    frame_interval: int
    file_pattern: str
    frame_files: list[str]


class VideoProcessor:
    """
    영상 프레임 추출기.
    
    파이프라인의 첫 번째 단계, 영상을 프레임 단위로 분리
    
    Attributes:
        target_fps: 추출 목표 FPS
        max_frames: 최대 추출 프레임 수
        
    Example:
        >>> processor = VideoProcessor(target_fps=10.0)
        >>> for idx, frame in processor.extract_frames("video.mp4"):
        ...     process(frame)
    """
    
    def __init__(
        self, 
        target_fps: Optional[float] = None,
        max_frames: Optional[int] = None
    ):
        """
        VideoProcessor 초기화.
        
        Args:
            target_fps: 추출할 FPS (None이면 설정값 사용)
            max_frames: 최대 프레임 수 (None이면 설정값 사용)
        """
        self.target_fps = target_fps or settings.TARGET_FPS
        self.max_frames = max_frames or settings.MAX_VIDEO_FRAMES
        self._supported_formats = set(settings.SUPPORTED_VIDEO_FORMATS)
        
        logger.info(
            f"VideoProcessor 초기화: target_fps={self.target_fps}, "
            f"max_frames={self.max_frames}"
        )
    
    def validate_video(self, video_path: str | Path) -> tuple[bool, str]:
        """
        영상 파일 유효성 검사.
        
        파일 존재 여부, 포맷, 메타데이터를 종합적으로 검증합니다.
        
        Args:
            video_path: 검사할 영상 파일 경로
            
        Returns:
            (유효 여부, 메시지) 튜플
            
        Example:
            >>> valid, msg = processor.validate_video("test.mp4")
            >>> if not valid:
            ...     raise VideoProcessingError(msg)
        """
        video_path = Path(video_path)
        
        # 1. 파일 존재 확인
        if not video_path.exists():
            return False, f"파일이 존재하지 않습니다: {video_path}"
        
        # 2. 파일 크기 확인
        if video_path.stat().st_size == 0:
            return False, "파일 크기가 0입니다"
        
        # 3. 확장자 확인
        if video_path.suffix.lower() not in self._supported_formats:
            return False, f"지원하지 않는 포맷: {video_path.suffix}"
        
        # 4. 메타데이터 검증
        try:
            info = self.get_video_info(video_path)
            
            if info.fps <= 0:
                return False, "유효하지 않은 FPS 값"
            
            if info.total_frames <= 0:
                return False, "프레임을 찾을 수 없습니다"
            
            if info.width <= 0 or info.height <= 0:
                return False, "유효하지 않은 해상도"
            
            if info.duration_sec > settings.MAX_VIDEO_DURATION_SEC:
                return False, f"영상이 너무 깁니다: {info.duration_sec:.1f}초 (최대 {settings.MAX_VIDEO_DURATION_SEC}초)"
            
            return True, "유효한 영상 파일"
            
        except Exception as e:
            return False, f"검증 중 오류: {str(e)}"
    
    def get_video_info(self, video_path: str | Path) -> VideoInfo:
        """
        영상 메타데이터 추출.
        (참고) fourcc : 현재 비디오 파일이 어떤 코덱을 사용하는지 그 식별 번호를 정수로 가져와라.
        
        Args:
            video_path: 영상 파일 경로
            
        Returns:
            VideoInfo 객체
            
        Raises:
            VideoProcessingError: 파일을 열 수 없거나 메타데이터 추출 실패
        """
        video_path = Path(video_path)
        
        if not video_path.exists():
            raise VideoProcessingError(
                f"파일을 찾을 수 없습니다: {video_path}",
                details={"path": str(video_path)}
            )
        
        cap = cv2.VideoCapture(str(video_path))
        
        if not cap.isOpened():
            raise VideoProcessingError(
                f"영상 파일을 열 수 없습니다: {video_path}",
                details={"path": str(video_path)}
            )
        
        try:
            fps = cap.get(cv2.CAP_PROP_FPS)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            fourcc = int(cap.get(cv2.CAP_PROP_FOURCC))
            
            return VideoInfo(
                path=str(video_path),
                filename=video_path.name,
                fps=fps,
                width=int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
                height=int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
                total_frames=total_frames,
                duration_sec=total_frames / fps if fps > 0 else 0,
                codec=self._decode_fourcc(fourcc)
            )
        finally:
            cap.release()
    
    def extract_frames(
        self,
        video_path: str | Path,
        start_sec: float = 0.0,
        end_sec: Optional[float] = None,
        validate: bool = True
    ) -> Generator[tuple[int, Image.Image], None, None]:
        """
        영상에서 프레임 추출 (Generator).
        
        메모리 효율을 위해 프레임을 하나씩 yield합니다.
        
        Args:
            video_path: 영상 파일 경로
            start_sec: 시작 시간 (초)
            end_sec: 종료 시간 (초, None이면 끝까지)
            validate: 사전 유효성 검사 여부
            
        Yields:
            (frame_index, PIL.Image) 튜플
            
        Raises:
            VideoProcessingError: 영상 처리 중 오류 발생
            
        Example:
            >>> for idx, frame in processor.extract_frames("video.mp4"):
            ...     keypoints = pose_model.detect(frame)
        """
        video_path = Path(video_path)
        
        # 사전 검증
        if validate:
            valid, msg = self.validate_video(video_path)
            if not valid:
                raise VideoProcessingError(msg, details={"path": str(video_path)})
        
        cap = cv2.VideoCapture(str(video_path))
        
        if not cap.isOpened():
            raise VideoProcessingError(f"영상을 열 수 없습니다: {video_path}")
        
        try:
            original_fps = cap.get(cv2.CAP_PROP_FPS)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            
            # 추출 간격 계산
            frame_interval = max(1, round(original_fps / self.target_fps))
            
            # 시작/종료 프레임 계산
            start_frame = int(start_sec * original_fps)
            end_frame = int(end_sec * original_fps) if end_sec else total_frames
            end_frame = min(end_frame, total_frames)
            
            # 시작 위치로 이동
            if start_frame > 0:
                cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
            
            logger.info(
                f"프레임 추출 시작: {video_path.name} "
                f"(fps: {original_fps:.1f}→{self.target_fps}, "
                f"interval: {frame_interval}, "
                f"range: {start_frame}-{end_frame})"
            )
            
            frame_idx = start_frame
            extracted_count = 0
            consecutive_failures = 0
            max_consecutive_failures = 10
            
            while extracted_count < self.max_frames and frame_idx < end_frame:
                ret, frame = cap.read()
                
                if not ret:
                    consecutive_failures += 1
                    if consecutive_failures >= max_consecutive_failures:
                        logger.warning(
                            f"연속 {max_consecutive_failures}회 읽기 실패, 추출 중단"
                        )
                        break
                    frame_idx += 1
                    continue
                
                consecutive_failures = 0
                
                # 간격에 맞는 프레임만 추출
                if (frame_idx - start_frame) % frame_interval == 0:
                    try:
                        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                        pil_image = Image.fromarray(rgb_frame)
                        
                        yield (extracted_count, pil_image)
                        extracted_count += 1
                        
                    except Exception as e:
                        logger.error(f"프레임 {frame_idx} 변환 오류: {e}")
                        continue
                
                frame_idx += 1
            
            logger.info(f"프레임 추출 완료: {extracted_count}개")
            
        finally:
            cap.release()
    
    def extract_frames_to_list(
        self,
        video_path: str | Path,
        **kwargs: Any
    ) -> list[tuple[int, Image.Image]]:
        """
        프레임을 리스트로 추출 (메모리 사용 주의).
        
        (작은 영상이나 테스트용으로만 사용)
        
        Args:
            video_path: 영상 파일 경로
            **kwargs: extract_frames에 전달할 추가 인자
            
        Returns:
            (frame_index, PIL.Image) 튜플 리스트
        """
        return list(self.extract_frames(video_path, **kwargs))
    
    def extract_frames_to_folder(
        self,
        video_path: str | Path,
        output_folder: str | Path,
        start_sec: float = 0.0,
        end_sec: Optional[float] = None,
        validate: bool = True,
        image_format: str = "jpg",
        quality: int = 95,
        clean_folder: bool = True
    ) -> FrameExtractionResult:
        """
        영상에서 프레임을 추출하여 폴더에 저장.
        
        영상을 프레임 단위로 분리하여 이미지로 저장합니다.
        
        Args:
            video_path: 영상 파일 경로
            output_folder: 프레임 이미지 저장 폴더
            start_sec: 시작 시간 (초)
            end_sec: 종료 시간 (초, None이면 끝까지)
            validate: 사전 유효성 검사 여부
            image_format: 이미지 포맷 ("jpg" 또는 "png")
            quality: JPEG 품질 (1-100)
            clean_folder: 기존 폴더 정리 여부
            
        Returns:
            FrameExtractionResult: 추출 결과 메타데이터
            
        Raises:
            VideoProcessingError: 영상 처리 중 오류 발생
            
        Example:
            >>> processor = VideoProcessor(target_fps=10.0)
            >>> result = processor.extract_frames_to_folder("video.mp4", "frames/")
            >>> print(f"저장된 프레임: {result.saved_count}개")
        """
        import shutil
        
        video_path = Path(video_path)
        output_folder = Path(output_folder)
        
        # 사전 검증
        if validate:
            valid, msg = self.validate_video(video_path)
            if not valid:
                raise VideoProcessingError(msg, details={"path": str(video_path)})
        
        # 출력 폴더 생성 (기존 파일 정리)
        if output_folder.exists() and clean_folder:
            shutil.rmtree(output_folder)
        output_folder.mkdir(parents=True, exist_ok=True)
        
        cap = cv2.VideoCapture(str(video_path))
        
        if not cap.isOpened():
            raise VideoProcessingError(f"영상을 열 수 없습니다: {video_path}")
        
        try:
            original_fps = cap.get(cv2.CAP_PROP_FPS)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            video_info = self.get_video_info(video_path)
            
            # 추출 간격 계산
            frame_interval = max(1, round(original_fps / self.target_fps))
            
            # 시작/종료 프레임 계산
            start_frame = int(start_sec * original_fps)
            end_frame = int(end_sec * original_fps) if end_sec else total_frames
            end_frame = min(end_frame, total_frames)
            
            if start_frame > 0:
                cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
            
            logger.info(
                f"프레임 추출 시작: {video_path.name} → {output_folder} "
                f"(fps: {original_fps:.1f}→{self.target_fps}, interval: {frame_interval})"
            )
            
            frame_idx = start_frame
            saved_count = 0
            saved_files: list[str] = []
            consecutive_failures = 0
            max_consecutive_failures = 10
            
            file_pattern = f"frame_{{:05d}}.{image_format}"
            
            while saved_count < self.max_frames and frame_idx < end_frame:
                ret, frame = cap.read()
                
                if not ret:
                    consecutive_failures += 1
                    if consecutive_failures >= max_consecutive_failures:
                        logger.warning(
                            f"연속 {max_consecutive_failures}회 읽기 실패, 추출 중단"
                        )
                        break
                    frame_idx += 1
                    continue
                
                consecutive_failures = 0
                
                # 간격에 맞는 프레임만 저장
                if (frame_idx - start_frame) % frame_interval == 0:
                    try:
                        filename = file_pattern.format(saved_count)
                        filepath = output_folder / filename
                        
                        # JPEG 품질 설정
                        if image_format.lower() == "jpg":
                            cv2.imwrite(
                                str(filepath), 
                                frame, 
                                [cv2.IMWRITE_JPEG_QUALITY, quality]
                            )
                        else:
                            cv2.imwrite(str(filepath), frame)
                        
                        saved_files.append(filename)
                        saved_count += 1
                        
                        # 진행 상황 로그 (50프레임마다)
                        if saved_count % 50 == 0:
                            logger.info(f"진행 중: {saved_count}프레임 저장됨...")
                            
                    except Exception as e:
                        logger.error(f"프레임 {frame_idx} 저장 오류: {e}")
                        continue
                
                frame_idx += 1
            
            logger.info(f"프레임 추출 완료: {saved_count}개 → {output_folder}")
            
            return FrameExtractionResult(
                output_folder=str(output_folder),
                video_info=video_info,
                saved_count=saved_count,
                frame_interval=frame_interval,
                file_pattern=file_pattern,
                frame_files=saved_files
            )
            
        finally:
            cap.release()
    
    @staticmethod
    def _decode_fourcc(fourcc: int) -> str:
        """
        FOURCC 코드를 문자열로 변환.
        
        Args:
            fourcc: 4바이트 코덱 코드
            
        Returns:
            코덱 문자열 (예: 'H264', 'XVID')
        """
        return "".join([chr((fourcc >> 8 * i) & 0xFF) for i in range(4)])
    
    # =========================================================================
    # 편의 메서드: 영상 → 폴더 → 자세 추출 통합
    # =========================================================================
    
    def process_video_to_poses(
        self,
        video_path: str | Path,
        output_folder: str | Path = "extracted_frames"
    ):
        """
        영상을 폴더로 추출하고 PoseExtractor를 호출할 준비.
        
        이 메서드는 프레임 추출만 수행합니다.
        자세 추출은 PoseExtractor.extract_from_video()를 권장합니다.
        
        Args:
            video_path: 영상 파일 경로
            output_folder: 프레임 저장 폴더
            
        Returns:
            FrameExtractionResult: 추출 결과
            
        Example:
            >>> processor = VideoProcessor()
            >>> result = processor.process_video_to_poses("video.mp4")
            >>> # 이후 PoseExtractor.extract_from_folder(result.output_folder) 호출
            
        Note:
            통합 파이프라인은 PoseExtractor.extract_from_video()를 사용하세요.
        """
        return self.extract_frames_to_folder(
            video_path=video_path,
            output_folder=output_folder
        )