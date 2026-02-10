# # AI/services/pose-estimation/app/pipeline/pose_extractor.py
"""
프레임별 자세 추정 모듈.

각 프레임에서 사람을 감지하고 관절 좌표를 추출합니다.
Top-down 방식
= 사람 감지 → 자세 추정 순서로 진행합니다.
"""

import numpy as np
import logging
from pathlib import Path
from PIL import Image
from typing import Generator, Optional
from dataclasses import dataclass, field

from app.models.vitpose import get_model
from app.config import settings
from app.pipeline.exceptions import PoseExtractionError

# 지연 로딩을 위함.
# from app.pipeline.video_processor import VideoProcessor, FrameExtractionResult

logger = logging.getLogger(__name__)


@dataclass
class VideoExtractionResult:
    """
    영상에서 추출한 자세 데이터 결과.
    
    VideoProcessor + PoseExtractor 통합 결과를 담는 데이터클래스.
    
    Attributes:
        frames_folder: 프레임 이미지 저장 폴더
        frame_count: 추출된 프레임 수
        valid_frame_count: 유효한 프레임 수
        frames_data: 프레임별 자세 데이터
        sequence: 주요 인물 키포인트 시퀀스 (N, NUM_KEYPOINTS, 3)
        video_fps: 원본 영상 FPS
        video_duration: 원본 영상 길이 (초)
    """
    frames_folder: str
    frame_count: int
    valid_frame_count: int
    frames_data: list  # list[FramePoseData]
    sequence: np.ndarray
    video_fps: float
    video_duration: float


# constants
PROGRESS_LOG_INTERVAL = 50
DEFAULT_IMAGE_QUALITY = 95
NUM_KEYPOINTS = 17

# VitPose 17 키포인트 정의
KEYPOINT_NAMES: list[str] = [
    "Nose", "L_Eye", "R_Eye", "L_Ear", "R_Ear",
    "L_Shoulder", "R_Shoulder", "L_Elbow", "R_Elbow",
    "L_Wrist", "R_Wrist", "L_Hip", "R_Hip",
    "L_Knee", "R_Knee", "L_Ankle", "R_Ankle"
]

# 키포인트 인덱스 상수
class KeypointIndex:
    """키포인트 인덱스 상수 정의."""
    NOSE = 0
    L_EYE, R_EYE = 1, 2
    L_EAR, R_EAR = 3, 4
    L_SHOULDER, R_SHOULDER = 5, 6
    L_ELBOW, R_ELBOW = 7, 8
    L_WRIST, R_WRIST = 9, 10
    L_HIP, R_HIP = 11, 12
    L_KNEE, R_KNEE = 13, 14
    L_ANKLE, R_ANKLE = 15, 16


@dataclass
class PersonPose:
    """
    개인별 자세 데이터.
    
    Attributes:
        person_id: 사람 식별자
        bbox: 바운딩 박스 [center_x, center_y, width, height]
        keypoints: 키포인트 딕셔너리
        confidence: 전체 신뢰도
        valid_keypoint_count: 유효한 키포인트 수
    """
    person_id: int
    bbox: list[float]
    keypoints: dict[str, dict[str, float]]
    confidence: float = 0.0
    valid_keypoint_count: int = 0


@dataclass
class FramePoseData:
    """
    프레임별 자세 데이터.
    
    Attributes:
        frame_idx: 프레임 인덱스
        persons: 감지된 사람 목록
        is_valid: 유효한 프레임 여부
    """
    frame_idx: int
    persons: list[PersonPose] = field(default_factory=list)
    is_valid: bool = True


class PoseExtractor:
    """
    자세 추정 추출기.
    
    프레임 시퀀스에서 관절 좌표를 추출합니다.
    
    Attributes:
        model: ViTPose 모델 인스턴스
        threshold: 감지 신뢰도 임계값
        min_valid_keypoints: 유효 프레임 판정 최소 키포인트 수
        
    Example:
        >>> extractor = PoseExtractor(threshold=0.3)
        >>> frames_data = extractor.extract_from_frames(frames_generator)
        >>> sequence = extractor.get_main_person_sequence(frames_data)
    """
    
    def __init__(
        self,
        threshold: Optional[float] = None,
        min_valid_keypoints: Optional[int] = None
    ):
        """
        PoseExtractor 초기화.
        
        Args:
            threshold: 감지 임계값 (None이면 설정값 사용)
            min_valid_keypoints: 최소 유효 키포인트 수
        """
        self.model = get_model()
        self.threshold = threshold or settings.DEFAULT_THRESHOLD
        self.min_valid_keypoints = min_valid_keypoints or settings.MIN_VALID_KEYPOINTS
        self.min_keypoint_score = settings.MIN_KEYPOINT_SCORE
        
        logger.info(
            f"PoseExtractor 초기화: threshold={self.threshold}, "
            f"min_valid_keypoints={self.min_valid_keypoints}"
        )
    
    def extract_from_frames(
        self,
        frames: Generator[tuple[int, Image.Image], None, None],
        skip_empty: bool = False
    ) -> list[FramePoseData]:
        """
        프레임 시퀀스에서 자세 추출.
        
        Args:
            frames: (frame_idx, PIL.Image) 생성기
            skip_empty: 사람 미감지 프레임 건너뛰기 여부
            
        Returns:
            FramePoseData 리스트
            
        Raises:
            PoseExtractionError: 모든 프레임에서 사람 미감지
        """
        results: list[FramePoseData] = []
        total_frames = 0
        valid_frames = 0
        
        for frame_idx, image in frames:
            total_frames += 1
            
            try:
                pose_results = self.model.detect(image, self.threshold)
                
                frame_data = FramePoseData(frame_idx=frame_idx)
                
                for person in pose_results:
                    person_pose = self._parse_person_result(person)
                    
                    # 유효성 판정
                    if person_pose.valid_keypoint_count >= self.min_valid_keypoints:
                        frame_data.persons.append(person_pose)
                
                if frame_data.persons:
                    valid_frames += 1
                    frame_data.is_valid = True
                else:
                    frame_data.is_valid = False
                    if skip_empty:
                        continue
                
                results.append(frame_data)
                
            except Exception as e:
                logger.warning(f"프레임 {frame_idx} 처리 실패: {e}")
                if not skip_empty:
                    results.append(FramePoseData(
                        frame_idx=frame_idx,
                        is_valid=False
                    ))
        
        # 결과 검증
        if total_frames == 0:
            raise PoseExtractionError("입력 프레임이 없습니다")
        
        validity_ratio = valid_frames / total_frames
        logger.info(
            f"자세 추출 완료: {valid_frames}/{total_frames} 유효 "
            f"({validity_ratio:.1%})"
        )
        
        if validity_ratio < settings.MIN_VALID_FRAME_RATIO:  # 10% 미만이면 경고
            logger.warning(f"유효 프레임 비율이 낮습니다: {validity_ratio:.1%}")
        
        return results
    
    def extract_from_folder(
        self,
        folder_path: str | Path,
        file_pattern: str = "frame_*.jpg",
        skip_empty: bool = False
    ) -> list[FramePoseData]:
        """
        폴더의 이미지 파일들에서 자세 추출.
        
        VideoProcessor.extract_frames_to_folder()로 저장된 프레임들을 처리합니다.
        
        Args:
            folder_path: 이미지 폴더 경로
            file_pattern: 파일 필터 패턴 (glob)
            skip_empty: 사람 미감지 프레임 건너뛰기 여부
            
        Returns:
            FramePoseData 리스트
            
        Raises:
            PoseExtractionError: 폴더가 없거나 이미지가 없는 경우
            
        Example:
            >>> extractor = PoseExtractor()
            >>> frames_data = extractor.extract_from_folder("extracted_frames/")
            >>> sequence = extractor.get_main_person_sequence(frames_data)
        """
        folder_path = Path(folder_path)
        
        if not folder_path.exists():
            raise PoseExtractionError(
                f"폴더를 찾을 수 없습니다: {folder_path}",
                details={"folder": str(folder_path)}
            )
        
        # 파일 정렬 (frame_00000.jpg, frame_00001.jpg, ...)
        image_files = sorted(folder_path.glob(file_pattern))
        
        if not image_files:
            raise PoseExtractionError(
                f"이미지 파일이 없습니다: {folder_path}/{file_pattern}",
                details={"folder": str(folder_path), "pattern": file_pattern}
            )
        
        logger.info(
            f"폴더에서 자세 추출 시작: {folder_path} ({len(image_files)}개 이미지)"
        )
        
        results: list[FramePoseData] = []
        valid_frames = 0
        total_frames = len(image_files)
        
        for frame_idx, image_path in enumerate(image_files):
            try:
                image = Image.open(image_path).convert("RGB")
                pose_results = self.model.detect(image, self.threshold)
                
                frame_data = FramePoseData(frame_idx=frame_idx)
                
                for person in pose_results:
                    person_pose = self._parse_person_result(person)
                    
                    if person_pose.valid_keypoint_count >= self.min_valid_keypoints:
                        frame_data.persons.append(person_pose)
                
                if frame_data.persons:
                    valid_frames += 1
                    frame_data.is_valid = True
                else:
                    frame_data.is_valid = False
                    if skip_empty:
                        continue
                
                results.append(frame_data)
                
                # 진행 상황 로그 (PROGRESS_LOG_INTERVAL 프레임마다)
                if (frame_idx + 1) % PROGRESS_LOG_INTERVAL == 0:
                    logger.info(f"진행 중: {frame_idx + 1}/{total_frames} 처리됨...")
                
            except Exception as e:
                logger.warning(f"이미지 {image_path.name} 처리 실패: {e}")
                if not skip_empty:
                    results.append(FramePoseData(frame_idx=frame_idx, is_valid=False))
        
        if not results:
            raise PoseExtractionError(
                "처리된 프레임이 없습니다",
                details={"folder": str(folder_path)}
            )
        
        validity_ratio = valid_frames / total_frames if total_frames > 0 else 0
        logger.info(
            f"폴더 자세 추출 완료: {valid_frames}/{total_frames} 유효 "
            f"({validity_ratio:.1%})"
        )
        
        if validity_ratio < settings.MIN_VALID_FRAME_RATIO:
            logger.warning(f"유효 프레임 비율이 낮습니다: {validity_ratio:.1%}")
        
        return results
    
    def get_main_person_sequence(
        self,
        frames_data: list[FramePoseData],
        interpolate: bool = True
    ) -> np.ndarray:
        """
        주요 인물의 관절 시퀀스 추출.
        
        가장 큰 바운딩 박스를 가진 사람을 주요 인물로 선정합니다.
        
        Args:
            frames_data: FramePoseData 리스트
            interpolate: 누락 프레임 보간 여부
            
        Returns:
            shape (num_frames, NUM_KEYPOINTS, 3) 배열 [x, y, score]
            
        Raises:
            PoseExtractionError: 유효한 프레임이 없음
        """
        if not frames_data:
            raise PoseExtractionError("프레임 데이터가 비어있습니다")
        
        sequences: list[np.ndarray] = []
        last_valid_keypoints: Optional[np.ndarray] = None
        
        for frame in frames_data:
            if frame.persons:
                # 가장 큰 bbox를 가진 사람 선택
                main_person = max(
                    frame.persons,
                    key=lambda p: p.bbox[2] * p.bbox[3]  # width * height
                )
                keypoints = self._person_to_array(main_person)
                last_valid_keypoints = keypoints
                sequences.append(keypoints)
                
            elif interpolate and last_valid_keypoints is not None:
                # 이전 프레임 값으로 대체 (점수는 0으로)
                interpolated = last_valid_keypoints.copy()
                interpolated[:, 2] = 0.0  # 보간된 프레임임을 표시
                sequences.append(interpolated)
                
            else:
                # 빈 프레임
                sequences.append(np.zeros((NUM_KEYPOINTS, 3)))
        
        result = np.array(sequences)
        
        # 유효성 검사
        valid_frames = np.sum(result[:, :, 2].max(axis=1) > 0)
        if valid_frames == 0:
            raise PoseExtractionError(
                "유효한 키포인트를 가진 프레임이 없습니다",
                details={"total_frames": len(frames_data)}
            )
        
        return result
    
    def _parse_person_result(self, person: dict) -> PersonPose:
        """
        모델 출력을 PersonPose로 변환.
        
        Args:
            person: 모델 출력 딕셔너리
            
        Returns:
            PersonPose 객체
        """
        keypoints_dict: dict[str, dict[str, float]] = {}
        valid_count = 0
        total_score = 0.0
        
        for kp in person.get("keypoints", []):
            name = kp["name"]
            score = kp["score"]
            
            keypoints_dict[name] = {
                "x": float(kp["x"]),
                "y": float(kp["y"]),
                "score": float(score)
            }
            
            if score >= self.min_keypoint_score:
                valid_count += 1
                total_score += score
        
        confidence = total_score / valid_count if valid_count > 0 else 0.0
        
        return PersonPose(
            person_id=person.get("person_id", 0),
            bbox=person.get("bbox", [0, 0, 0, 0]),
            keypoints=keypoints_dict,
            confidence=confidence,
            valid_keypoint_count=valid_count
        )
    
    def _person_to_array(self, person: PersonPose) -> np.ndarray:
        """
        PersonPose를 numpy 배열로 변환.
        
        Args:
            person: PersonPose 객체
            
        Returns:
            shape (NUM_KEYPOINTS, 3) 배열 [x, y, score]
        """
        result = np.zeros((NUM_KEYPOINTS, 3))
        
        for i, name in enumerate(KEYPOINT_NAMES):
            if name in person.keypoints:
                kp = person.keypoints[name]
                result[i] = [kp["x"], kp["y"], kp["score"]]
        
        return result
    
    # =========================================================================
    # 통합 메서드: 영상 → 폴더 → 키포인트 시퀀스
    # =========================================================================
    
    def extract_from_video(
        self,
        video_path: str | Path,
        output_folder: str | Path = "extracted_frames",
        target_fps: Optional[float] = None,
        max_frames: Optional[int] = None,
        keep_frames: bool = True,
        skip_empty: bool = False,
        interpolate: bool = True
    ) -> VideoExtractionResult:
        """
        영상에서 직접 키포인트 시퀀스 추출 (통합 파이프라인).
        
        VideoProcessor로 프레임 추출 → PoseExtractor로 자세 추출 → 시퀀스 반환.
        test_folder_mode_standalone.py의 로직을 모듈 내부로 통합.
        
        Args:
            video_path: 영상 파일 경로
            output_folder: 프레임 이미지 저장 폴더
            target_fps: 추출 목표 FPS (None이면 설정값 사용)
            max_frames: 최대 프레임 수 (None이면 설정값 사용)
            keep_frames: 추출한 프레임 이미지 유지 여부
            skip_empty: 사람 미감지 프레임 건너뛰기
            interpolate: 누락 프레임 보간 여부
            
        Returns:
            VideoExtractionResult: 통합 결과 (시퀀스 + 메타데이터)
            
        Example:
            >>> extractor = PoseExtractor()
            >>> result = extractor.extract_from_video("video.mp4")
            >>> print(f"시퀀스 shape: {result.sequence.shape}")
            >>> print(f"유효 프레임: {result.valid_frame_count}/{result.frame_count}")
        """
        import shutil
        from app.pipeline.video_processor import VideoProcessor
        
        video_path = Path(video_path)
        output_folder = Path(output_folder)
        
        # 설정값 로드
        target_fps = target_fps or settings.TARGET_FPS
        max_frames = max_frames or settings.MAX_VIDEO_FRAMES
        
        logger.info(f"통합 파이프라인 시작: {video_path} → {output_folder}")
        
        # Step 1: VIDEO → FRAMES (폴더 저장)
        logger.info("[Step 1] 영상에서 프레임 추출 중...")
        processor = VideoProcessor(target_fps=target_fps, max_frames=max_frames)
        
        extraction_result = processor.extract_frames_to_folder(
            video_path=video_path,
            output_folder=output_folder,
            image_format="jpg",
            quality=DEFAULT_IMAGE_QUALITY
        )
        
        logger.info(
            f"👶 [Step 1] 완료: {extraction_result.saved_count}개 프레임 저장 "
            f"(interval={extraction_result.frame_interval})"
        )
        
        # Step 2: FRAMES → POSE (폴더에서 자세 추출)
        logger.info(" 🧒 [Step 2] 폴더에서 자세 추출 중...")
        frames_data = self.extract_from_folder(
            folder_path=output_folder,
            skip_empty=skip_empty
        )
        
        valid_count = sum(1 for f in frames_data if f.is_valid)
        logger.info(f"🧑 [Step 2] 완료: {valid_count}/{len(frames_data)} 유효 프레임")
        
        # Step 3: POSE → SEQUENCE (주요 인물 시퀀스)
        logger.info(" 👨 [Step 3] 주요 인물 시퀀스 추출 중...")
        sequence = self.get_main_person_sequence(
            frames_data=frames_data,
            interpolate=interpolate
        )
        logger.info(f"🧔 [Step 3] 완료: 시퀀스 shape={sequence.shape}")
        
        # 프레임 정리 (선택적)
        if not keep_frames and output_folder.exists():
            shutil.rmtree(output_folder)
            logger.info(f"프레임 폴더 정리: {output_folder}")
        
        result = VideoExtractionResult(
            frames_folder=str(output_folder) if keep_frames else "",
            frame_count=extraction_result.saved_count,
            valid_frame_count=valid_count,
            frames_data=frames_data,
            sequence=sequence,
            video_fps=extraction_result.video_info.fps,
            video_duration=extraction_result.video_info.duration_sec
        )
        
        logger.info(
            f"통합 파이프라인 완료: "
            f"{result.frame_count}프레임, "
            f"{result.valid_frame_count}유효, "
            f"shape={result.sequence.shape}"
        )
        
        return result