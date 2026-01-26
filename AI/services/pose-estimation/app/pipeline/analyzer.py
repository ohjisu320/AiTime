# AI/services/pose-estimation/app/pipeline/analyzer.py
"""
개별적으로 구현된 
영상 처리, 자세 추출, 정규화, 시간 정렬(DTW), 유사도 계산 모듈들을 
하나로 조합하여 
최종적인 동작 분석 서비스를 제공하는
 통합 파이프라인

FastAPI 엔드포인트에서 직접 호출하는 진입점

[주요 구성 요소]
1. AnalysisResult 데이터 클래스
    - 분석 결과를 구조화하여 API 응답에 적합한 형태로 제공
        - 통과 여부(`passed`)
        - 유사도 점수(`similarity_score`)
        - 반응 지연 시간(`reaction_delay_sec`)
        - 동작 지속 시간(`duration_sec`)
        - 분석 유효성 점수(`validity`) 
        등.
2. MotionAnalyzer 코어 클래스
    - 전체 파이프라인을 관리
    - 지원 동작: `clapping`, `hurray`, `walking_back`, `jumping`, `kicking`, `throwing`.
    - 내부 모듈: `VideoProcessor`, `PoseExtractor`, `PoseNormalizer`, `DTWAligner`, `SimilarityCalculator`

[주요 기능]    
1. `analyze()`: 
   - 영상 경로와 동작 타입을 입력받아 전체 분석 수행.
   - 순서: 입력 검증 → 프레임 추출 → 자세 추출 → 정규화/역할 식별 → 반응 지연 계산 → DTW 정렬 → 유사도 계산 → 결과 집계.
2. `analyze_with_visualization()`:
   - 분석과 동시에 스켈레톤 시각화 수행.
   - 부모(Blue)와 아이(Orange)를 구분한 시각화 프레임 및 동영상(`.mp4`) 추출.    

[ CLI 사용법 ]
```bash
python -m app.pipeline.analyzer <video_path> <action_type> --age <months> --visualize
```
"""

import logging
import numpy as np
from pathlib import Path
from typing import Optional, Any
from datetime import datetime
from dataclasses import dataclass, asdict, field

from app.config import settings
from app.pipeline.video_processor import VideoProcessor
from app.pipeline.pose_extractor import PoseExtractor
from app.pipeline.normalizer import PoseNormalizer
from app.pipeline.dtw import DTWAligner
from app.pipeline.similarity import SimilarityCalculator, ActionWeightPresets
from app.pipeline.exceptions import (
    PipelineError,
    InvalidInputError
)

logger = logging.getLogger(__name__)


# ==================== 상수 정의 ====================
# 반응 지연 및 지속 시간 계산
DEFAULT_REACTION_DELAY_THRESHOLD = 0.65  # 동작 시작 판정 기본 임계값
DEFAULT_DURATION_THRESHOLD = 0.5  # 동작 지속 판정 기본 임계값

# 유사도 계산
EPSILON_NORM_CHECK = 1e-8  # 정규화 벡터 크기 체크용 엡실론

# 만세 동작 감지
HURRAY_WRIST_MARGIN = 0.3  # 손목이 어깨 위로 올라가야 하는 거리 (정규화 좌표)

# 프레임 파일 포맷
FRAME_FILENAME_PATTERN = "frame_{:05d}.jpg"  # 추출된 프레임 파일명
VISUALIZED_FILENAME_PATTERN = "viz_{:05d}.jpg"  # 시각화된 프레임 파일명
TEMP_FOLDER_PREFIX = "pose_frames_"  # 임시 폴더 접두사

# 폴더명
EXTRACTED_FRAMES_FOLDER = "extracted_frames"
VISUALIZED_FRAMES_FOLDER = "visualized_frames"

# 비디오 코덱
VIDEO_FOURCC = 'mp4v'  # MP4 비디오 코덱

# 파일 확장자
IMAGE_EXTENSION = ".jpg"
VIDEO_EXTENSION = ".mp4"
# ================================================


@dataclass
class AnalysisResult:
    """
    분석 결과 데이터.
    
    Attributes:
        passed: 통과 여부
        similarity_score: 전체 유사도 점수
        reaction_delay_sec: 반응 지연 시간 (초)
        duration_sec: 동작 수행 시간 (초)
        validity: 분석 유효성 점수
        threshold_used: 적용된 통과 기준
        action_type: 동작 유형
        age_months: 아동 월령
        processing_time_sec: 처리 소요 시간
        details: 상세 분석 정보
        visualization_info: 시각화 관련 정보 (옵션)
        role_info: 부모/아이 역할 정보 (옵션)
    """
    passed: bool
    similarity_score: float
    reaction_delay_sec: float
    duration_sec: float
    validity: float
    threshold_used: float
    action_type: str
    age_months: int
    processing_time_sec: float
    details: dict[str, Any]
    visualization_info: Optional[dict[str, Any]] = field(default=None)
    role_info: Optional[dict[str, Any]] = field(default=None)
    
    def to_dict(self) -> dict[str, Any]:
        """
        딕셔너리로 변환.
        
        Returns:
            API 응답용 딕셔너리
        """
        result = asdict(self)
        
        # numpy 타입을 Python 기본 타입으로 변환
        result["passed"] = bool(result["passed"])
        result["similarity_score"] = float(round(result["similarity_score"], 4))
        result["validity"] = float(round(result["validity"], 4))
        result["reaction_delay_sec"] = float(round(result["reaction_delay_sec"], 2))
        result["duration_sec"] = float(round(result["duration_sec"], 2))
        result["processing_time_sec"] = float(round(result["processing_time_sec"], 2))
        result["threshold_used"] = float(result["threshold_used"])
        result["age_months"] = int(result["age_months"])
        
        # details 내부의 numpy 타입도 변환
        if result.get("details"):
            for key, value in result["details"].items():
                if hasattr(value, 'item'):  # numpy scalar
                    result["details"][key] = value.item()
                elif isinstance(value, (int, float, bool, str, type(None))):
                    pass
                else:
                    try:
                        result["details"][key] = float(value)
                    except (TypeError, ValueError):
                        result["details"][key] = str(value)
        
        # role_info 내부의 numpy 타입도 변환
        if result.get("role_info"):
            result["role_info"] = self._convert_numpy_types(result["role_info"])
        
        return result
    
    def _convert_numpy_types(self, obj: Any) -> Any:
        """numpy 타입을 Python 기본 타입으로 재귀 변환"""
        import numpy as np
        
        if isinstance(obj, dict):
            return {k: self._convert_numpy_types(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._convert_numpy_types(v) for v in obj]
        elif isinstance(obj, np.bool_):
            return bool(obj)
        elif isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        else:
            return obj


class MotionAnalyzer:
    """
    동작 모방행동 분석 파이프라인.
    
    영상 입력을 받아 기준 동작과의 유사도를 분석합니다.
    
    Attributes:
        video_processor: 영상 처리기
        pose_extractor: 자세 추출기
        normalizer: 정규화기
        dtw_aligner: DTW 정렬기
        similarity_calculator: 유사도 계산기
        references: 기준 동작 데이터
        
    Example:
        >>> analyzer = MotionAnalyzer()
        >>> result = analyzer.analyze("video.mp4", "clapping", 15)
        >>> print(f"Pass: {result.passed}, Score: {result.similarity_score:.2%}")
    """
    
    # 지원하는 동작 목록
    SUPPORTED_ACTIONS = [
        "clapping", "hurray", "walking_back",
        "jumping", "kicking", "throwing"
    ]
    
    # 월령 범위
    MIN_AGE_MONTHS = 12
    MAX_AGE_MONTHS = 24
    
    def __init__(self, use_folder_mode: bool = False, frames_folder: Optional[str] = None):
        """
        MotionAnalyzer 초기화.
        
        모든 파이프라인 모듈을 초기화하고 기준 데이터를 로드합니다.
        
        Args:
            use_folder_mode: True면 폴더 저장 방식, False면 기존 Generator 방식
            frames_folder: 프레임 저장 폴더 (None이면 임시 폴더 사용)
        """
        logger.info("MotionAnalyzer 초기화 중...")
        
        self.use_folder_mode = use_folder_mode
        self.frames_folder = frames_folder
        
        self.video_processor = VideoProcessor()
        self.pose_extractor = PoseExtractor()
        self.normalizer = PoseNormalizer()
        self.dtw_aligner = DTWAligner()
        self.similarity_calculator = SimilarityCalculator()
        
        logger.info(
            f"MotionAnalyzer 초기화 완료. "
            f"모드: {'폴더 저장' if use_folder_mode else 'Generator'}"
        )
    
    def analyze(
        self,
        video_path: str,
        action_type: str,
        age_months: int,
        reference_sequence: Optional[np.ndarray] = None,
        use_parent_reference: bool = True,
        identify_roles: bool = True,
        smooth: bool = True,
        smooth_method: str = "one_euro"
    ) -> AnalysisResult:
        """
        동작 분석 메인 함수.
        
        전체 파이프라인을 실행하여 동작 유사도를 분석합니다.
        
        Args:
            video_path: 분석할 영상 경로
            action_type: 동작 유형 ("clapping", "hurray" 등)
            age_months: 아동 월령 (12-36)
            reference_sequence: 커스텀 기준 시퀀스 (None이면 기본값 사용)
            use_parent_reference: 부모 동작을 기준으로 사용할지 여부 (기본: True)
            identify_roles: 부모/아이 역할 구분 활성화
            smooth: 스무딩 적용 여부
            smooth_method: 스무딩 방법 ("one_euro", "exponential", "moving_avg")
            
        Returns:
            AnalysisResult 객체
            
        Raises:
            InvalidInputError: 잘못된 입력값
            ReferenceNotFoundError: 기준 데이터 없음
            PipelineError: 파이프라인 처리 오류
        """
        start_time = datetime.now()
        
        # 동작별 가중치 프리셋 적용
        weights = ActionWeightPresets.get(action_type)
        self.similarity_calculator = SimilarityCalculator(**weights)
        logger.debug(f"동작별 가중치 프리셋 적용: {action_type} -> {weights}")
        
        # 1. 입력 검증
        self._validate_input(action_type, age_months)
        
        try:
            # 2. VIDEO TO IMG
            logger.info(f"영상 처리 시작: {video_path}")
            
            if self.use_folder_mode:
                # 폴더 저장 방식: 프레임을 이미지로 저장 후 처리
                import tempfile
                import shutil
                
                if self.frames_folder:
                    output_folder = Path(self.frames_folder)
                else:
                    output_folder = Path(tempfile.mkdtemp(prefix=TEMP_FOLDER_PREFIX))
                
                extraction_result = self.video_processor.extract_frames_to_folder(
                    video_path,
                    output_folder=output_folder
                )
                video_info = extraction_result.video_info
                
                # 3. 2D POSE ESTIMATION (폴더에서 읽기)
                logger.info(f"자세 추출 중... (폴더: {output_folder})")
                frames_data = self.pose_extractor.extract_from_folder(output_folder)
                
                # 임시 폴더 정리 (지정 폴더가 아닌 경우에만)
                if not self.frames_folder and output_folder.exists():
                    shutil.rmtree(output_folder)
                    logger.debug(f"임시 폴더 정리: {output_folder}")
            else:
                # Generator 방식: 기존 메모리 효율적 처리
                video_info = self.video_processor.get_video_info(video_path)
                frames = self.video_processor.extract_frames(video_path)
                
                # 3. 2D POSE ESTIMATION
                logger.info("자세 추출 중...")
                frames_data = self.pose_extractor.extract_from_frames(frames)
            
            # 4. NORMALIZATION with role identification and smoothing
            logger.info("정규화 및 역할 식별 중...")
            
            norm_result = self.normalizer.normalize_and_smooth(
                frames_data=frames_data,
                identify_roles=identify_roles,
                smooth=smooth,
                smooth_method=smooth_method
            )
            
            # 역할 정보 저장
            role_info = None
            frame_persons = norm_result.get("frame_persons", [])
            if frame_persons and len(frame_persons) > 0:
                first_frame = frame_persons[0]
                role_info = {
                    "parent_identified": first_frame.parent is not None,
                    "child_identified": first_frame.child is not None,
                    "parent_torso_length": first_frame.parent.torso_length if first_frame.parent else None,
                    "child_torso_length": first_frame.child.torso_length if first_frame.child else None,
                }
            
            # 아이 시퀀스를 query로 사용 (없으면 부모 시퀀스)
            child_seq = norm_result.get("child_sequence")
            parent_seq = norm_result.get("parent_sequence")
            
            # 부모 시퀀스 필수 체크
            if parent_seq is None:
                raise PipelineError(
                    message="부모 시퀀스를 감지하지 못했습니다. 부모와 아이가 함께 있는 영상이 필요합니다.",
                    code="PARENT_NOT_DETECTED",
                    details={"video_path": video_path}
                )
            
            # 아이 시퀀스 필수 체크
            if child_seq is None:
                raise PipelineError(
                    message="아이 시퀀스를 감지하지 못했습니다. 부모와 아이가 함께 있는 영상이 필요합니다.",
                    code="CHILD_NOT_DETECTED",
                    details={"video_path": video_path}
                )
            
            # 부모-아이 분석 진행
            query_normalized = child_seq
            ref_normalized = parent_seq
            logger.info("부모-아이 시퀀스 분석 시작")
            
            # 5. 반응 지연 계산 (DTW 정렬 전 - 부모-아이 상대 시간)
            threshold = settings.get_action_threshold(action_type)
            reaction_delay_detail = None
            
            # 부모-아이 모두 감지됨 → 상대 반응 지연 계산
            reaction_delay, reaction_delay_detail = self._calculate_reaction_delay_from_parent(
                parent_sequence=parent_seq,
                child_sequence=child_seq,
                ref_sequence=parent_seq,  # 부모 시퀀스를 참조로 사용
                fps=video_info.fps,
                threshold=threshold,
                action_type=action_type
            )
            
            # 6. DTW ALIGNMENT
            logger.info("시간 정렬 중...")
            aligned_query, aligned_ref = self.dtw_aligner.align_sequences(
                query_normalized, ref_normalized
            )
            
            # 7. SIMILARITY CALCULATION
            logger.info("유사도 계산 중...")
            similarity_result = self.similarity_calculator.compute_similarity(
                aligned_query, aligned_ref, aligned=True
            )
            
            # 8. 지속 시간 계산 (정렬 후 유사도 기반)
            duration = self._calculate_duration(
                similarity_result.frame_similarities,
                video_info.fps,
                threshold=threshold
            )
            
            validity = self._calculate_validity(query_normalized)
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # role_info에 반응 지연 상세 정보 추가
            if role_info and reaction_delay_detail:
                role_info["reaction_delay_detail"] = reaction_delay_detail
            
            result = AnalysisResult(
                passed=similarity_result.overall >= threshold,
                similarity_score=similarity_result.overall,
                reaction_delay_sec=reaction_delay,
                duration_sec=duration,
                validity=validity,
                threshold_used=threshold,
                action_type=action_type,
                age_months=age_months,
                processing_time_sec=processing_time,
                role_info=role_info,
                details={
                    "upper_body_score": similarity_result.upper_body,
                    "lower_body_score": similarity_result.lower_body,
                    "head_score": similarity_result.head,
                    "total_frames_analyzed": len(frames_data),
                    "valid_frame_ratio": similarity_result.valid_frame_ratio,
                    "video_duration_sec": video_info.duration_sec,
                    "video_fps": video_info.fps,
                    "use_parent_reference": use_parent_reference,
                    "smooth_method": smooth_method if smooth else None
                }
            )
            
            logger.info(
                f"분석 완료: pass={result.passed}, "
                f"score={result.similarity_score:.4f}, "
                f"time={processing_time:.2f}s"
            )
            
            return result
            
        except PipelineError:
            raise
        except Exception as e:
            logger.error(f"분석 중 예외 발생: {e}", exc_info=True)
            raise PipelineError(
                message=f"분석 중 오류 발생: {str(e)}",
                code="ANALYSIS_ERROR",
                details={"video_path": video_path, "action_type": action_type}
            )
    
    def _validate_input(self, action_type: str, age_months: int) -> None:
        """
        입력값 유효성 검사.
        
        Args:
            action_type: 동작 유형
            age_months: 월령
            
        Raises:
            InvalidInputError: 유효하지 않은 입력
        """
        if action_type not in self.SUPPORTED_ACTIONS:
            raise InvalidInputError(
                message=f"지원하지 않는 동작입니다: {action_type}",
                field="action_type",
                value=action_type
            )
        
        if not (self.MIN_AGE_MONTHS <= age_months <= self.MAX_AGE_MONTHS):
            raise InvalidInputError(
                message=f"월령 범위 초과: {age_months} (허용: {self.MIN_AGE_MONTHS}-{self.MAX_AGE_MONTHS})",
                field="age_months",
                value=age_months
            )
    

    

    
    def _calculate_reaction_delay(
        self,
        frame_similarities: list[float],
        fps: float,
        start_threshold: float = DEFAULT_REACTION_DELAY_THRESHOLD
    ) -> float:
        """
        반응 지연 시간 계산.
        
        첫 유효 동작이 감지될 때까지의 시간을 계산합니다.
        유사도가 threshold를 처음으로 넘는 프레임까지의 시간.
        
        Args:
            frame_similarities: 프레임별 유사도 (0~1)
            fps: 영상 FPS
            start_threshold: 유효 동작 판정 임계값 (동작별 threshold 권장)
            
        Returns:
            반응 지연 시간 (초). 첫 프레임부터 동작이면 0.0
        """
        for i, sim in enumerate(frame_similarities):
            if sim >= start_threshold:
                return i / fps
        # 끝까지 threshold 미달 → 전체 영상 길이 반환
        return len(frame_similarities) / fps
    
    def _calculate_duration(
        self,
        frame_similarities: list[float],
        fps: float,
        threshold: float = DEFAULT_DURATION_THRESHOLD
    ) -> float:
        """
        유효 동작 지속 시간 계산.
        
        Args:
            frame_similarities: 프레임별 유사도
            fps: 영상 FPS
            threshold: 유효 동작 판정 임계값
            
        Returns:
            지속 시간 (초)
        """
        valid_frames = sum(1 for sim in frame_similarities if sim >= threshold)
        return valid_frames / fps
    
    def _quick_frame_similarity(
        self,
        frame1: np.ndarray,
        frame2: np.ndarray
    ) -> float:
        """
        두 프레임 간 빠른 코사인 유사도 계산.
        
        Args:
            frame1: 첫 번째 프레임 (17, 3)
            frame2: 두 번째 프레임 (17, 3)
            
        Returns:
            유사도 (0~1)
        """
        f1 = frame1[:, :2].flatten()
        f2 = frame2[:, :2].flatten()
        
        n1, n2 = np.linalg.norm(f1), np.linalg.norm(f2)
        if n1 < EPSILON_NORM_CHECK or n2 < EPSILON_NORM_CHECK:
            return 0.0
        
        cos = np.dot(f1, f2) / (n1 * n2)
        return float((cos + 1) / 2)  # -1~1 → 0~1
    
    def _detect_action_start_frame(
        self,
        sequence: np.ndarray,
        ref_sequence: np.ndarray,
        threshold: float,
        action_type: str = "hurray"
    ) -> int:
        """
        시퀀스에서 동작이 시작되는 프레임 인덱스 감지.
        
        동작 타입에 따라 다른 감지 방법을 사용합니다:
        - hurray: 손목이 어깨 위로 올라간 시점 (더 정확함)
        - 기타: 유사도 기반 감지
        
        Args:
            sequence: 분석할 시퀀스 (T, 17, 3)
            ref_sequence: 참조 동작 시퀀스 (T_ref, 17, 3)
            threshold: 동작 시작 판정 임계값
            action_type: 동작 타입
            
        Returns:
            동작 시작 프레임 인덱스. 동작 미시작 시 시퀀스 길이 반환.
        """
        if action_type == "hurray":
            return self._detect_hurray_start_frame(sequence)
        
        # 기타 동작: 유사도 기반 감지
        ref_mid = ref_sequence[len(ref_sequence) // 2]
        
        for i, frame in enumerate(sequence):
            sim = self._quick_frame_similarity(frame, ref_mid)
            if sim >= threshold:
                return i
        
        return len(sequence)
    
    def _detect_hurray_start_frame(
        self,
        sequence: np.ndarray,
        margin: float = HURRAY_WRIST_MARGIN
    ) -> int:
        """
        만세 동작 시작 프레임 감지 (손목 위치 기반).
        
        손목이 어깨보다 일정 거리 이상 위에 올라간 첫 프레임을 감지합니다.
        코사인 유사도보다 정확하게 만세 동작을 감지할 수 있습니다.
        
        Args:
            sequence: 분석할 시퀀스 (T, 17, 3)
            margin: 어깨 대비 손목이 얼마나 위에 있어야 하는지 (정규화 좌표 기준)
            
        Returns:
            만세 시작 프레임 인덱스. 미감지 시 시퀀스 길이 반환.
        """
        # COCO 키포인트: 5=L_Shoulder, 6=R_Shoulder, 9=L_Wrist, 10=R_Wrist
        # y 좌표: 정규화 후 위로 갈수록 음수
        
        for i, frame in enumerate(sequence):
            l_shoulder_y = frame[5, 1]
            r_shoulder_y = frame[6, 1]
            l_wrist_y = frame[9, 1]
            r_wrist_y = frame[10, 1]
            
            # 양쪽 손목이 모두 어깨보다 margin 이상 위에 있어야 함
            l_above = l_wrist_y < (l_shoulder_y - margin)
            r_above = r_wrist_y < (r_shoulder_y - margin)
            
            if l_above and r_above:
                return i
        
        return len(sequence)
    
    def _calculate_reaction_delay_from_parent(
        self,
        parent_sequence: np.ndarray,
        child_sequence: np.ndarray,
        ref_sequence: np.ndarray,
        fps: float,
        threshold: float,
        action_type: str = "hurray"
    ) -> tuple[float, dict]:
        """
        부모 대비 아이의 반응 지연 계산.
        
        부모가 동작을 시작한 시점과 아이가 동작을 시작한 시점의 차이를 계산합니다.
        
        Args:
            parent_sequence: 부모 시퀀스 (T, 17, 3)
            child_sequence: 아이 시퀀스 (T, 17, 3)
            ref_sequence: 참조 동작 시퀀스 (hurray.json 등)
            fps: 영상 FPS
            threshold: 동작 시작 판정 임계값
            action_type: 동작 타입 (hurray, clapping 등)
            
        Returns:
            (반응 지연 초, 상세 정보 dict)
            - 양수: 아이가 부모보다 늦게 시작 (정상)
            - 0: 동시 시작
            - 음수: 아이가 먼저 시작 (비정상)
        """
        # 부모 동작 시작 프레임
        parent_start = self._detect_action_start_frame(
            parent_sequence, ref_sequence, threshold, action_type
        )
        
        # 아이 동작 시작 프레임
        child_start = self._detect_action_start_frame(
            child_sequence, ref_sequence, threshold, action_type
        )
        
        # 반응 지연 계산
        delay_frames = child_start - parent_start
        delay_sec = delay_frames / fps
        
        # 상세 정보
        detail = {
            "parent_start_frame": parent_start,
            "parent_start_sec": parent_start / fps,
            "child_start_frame": child_start,
            "child_start_sec": child_start / fps,
            "delay_frames": delay_frames,
            "detection_method": "wrist_position" if action_type == "hurray" else "similarity"
        }
        
        logger.info(
            f"반응 지연 분석: 부모 시작={parent_start}프레임({parent_start/fps:.2f}초), "
            f"아이 시작={child_start}프레임({child_start/fps:.2f}초), "
            f"지연={delay_sec:.2f}초 (방식: {detail['detection_method']})"
        )
        
        return delay_sec, detail
    


    def _calculate_validity(self, sequence: np.ndarray) -> float:
        """
        분석 유효성 점수 계산.
        
        평균 키포인트 신뢰도를 기반으로 합니다.
        
        Args:
            sequence: 관절 시퀀스 (T, 17, 3)
            
        Returns:
            유효성 점수 (0~1)
        """
        scores = sequence[:, :, 2]  # 모든 프레임의 score
        valid_scores = scores[scores > settings.MIN_KEYPOINT_SCORE]
        
        if len(valid_scores) == 0:
            return 0.0
        
        return float(np.mean(valid_scores))
    
    def analyze_with_visualization(
        self,
        video_path: str,
        action_type: str,
        age_months: int,
        output_folder: str = "analysis_output",
        save_skeleton_video: bool = True,
        reference_sequence: Optional[np.ndarray] = None,
        use_parent_reference: bool = True,
        identify_roles: bool = True,
        smooth: bool = True,
        smooth_method: str = "one_euro"
    ) -> AnalysisResult:
        """
        동작 분석 + 스켈레톤 시각화 (역할 기반 색상 다르게 처리함!).
        
        분석과 함께 스켈레톤 오버레이 이미지와 동영상을 생성합니다.
        부모/아이 역할에 따라 다른 색상으로 시각화됩니다.
        
        Args:
            video_path: 분석할 영상 경로
            action_type: 동작 유형 ("clapping", "hurray" 등)
            age_months: 아동 월령 (12-36)
            output_folder: 시각화 결과 저장 폴더
            save_skeleton_video: 스켈레톤 동영상 저장 여부
            reference_sequence: 커스텀 기준 시퀀스
            use_parent_reference: 부모 시퀀스를 참조로 사용할지 여부 (기본: True)
            identify_roles: 부모/아이 역할 식별 여부
            smooth: 스무딩 적용 여부
            smooth_method: 스무딩 방법 ("one_euro", "ema", "moving_average")
            
        Returns:
            AnalysisResult (visualization_info, role_info 포함)
        """
        start_time = datetime.now()
        output_path = Path(output_folder)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # 동작별 가중치 프리셋 적용
        weights = ActionWeightPresets.get(action_type)
        self.similarity_calculator = SimilarityCalculator(**weights)
        logger.debug(f"동작별 가중치 프리셋 적용: {action_type} -> {weights}")
        
        # 하위 폴더 생성
        frames_folder = output_path / EXTRACTED_FRAMES_FOLDER
        viz_folder = output_path / VISUALIZED_FRAMES_FOLDER
        frames_folder.mkdir(exist_ok=True)
        viz_folder.mkdir(exist_ok=True)
        
        # 1. 입력 검증
        self._validate_input(action_type, age_months)
        
        try:
            # 2. 영상 → 프레임 폴더
            logger.info(f"영상 처리 시작: {video_path}")
            extraction_result = self.video_processor.extract_frames_to_folder(
                video_path,
                output_folder=frames_folder
            )
            video_info = extraction_result.video_info
            logger.info(f"프레임 추출 완료: {extraction_result.saved_count}개")
            
            # 4. 자세 추출
            logger.info(f"자세 추출 중... (폴더: {frames_folder})")
            frames_data = self.pose_extractor.extract_from_folder(frames_folder)
            
            valid_count = sum(1 for f in frames_data if f.is_valid)
            logger.info(f"자세 추출 완료: {valid_count}/{len(frames_data)} 유효")
            
            # 4. NORMALIZATION with role identification and smoothing
            logger.info("정규화 및 역할 식별 중...")
            
            norm_result = self.normalizer.normalize_and_smooth(
                frames_data=frames_data,
                identify_roles=identify_roles,
                smooth=smooth,
                smooth_method=smooth_method
            )
            
            # 역할 정보 저장
            role_info = None
            frame_persons = norm_result.get("frame_persons", [])
            if frame_persons and len(frame_persons) > 0:
                first_frame = frame_persons[0]
                role_info = {
                    "parent_identified": first_frame.parent is not None,
                    "child_identified": first_frame.child is not None,
                    "parent_torso_length": first_frame.parent.torso_length if first_frame.parent else None,
                    "child_torso_length": first_frame.child.torso_length if first_frame.child else None,
                }
            
            # 5. 역할 기반 스켈레톤 시각화
            logger.info("역할 기반 스켈레톤 시각화 중...")
            viz_count = self._visualize_frames_with_roles(
                frames_folder, frames_data, viz_folder, frame_persons
            )
            logger.info(f"시각화 완료: {viz_count}개 이미지")
            
            # 6. 스켈레톤 동영상 생성
            skeleton_video_path = None
            if save_skeleton_video:
                skeleton_video_path = output_path / "skeleton_video.mp4"
                self._create_skeleton_video(
                    viz_folder, 
                    skeleton_video_path, 
                    fps=self.video_processor.target_fps
                )
                logger.info(f"동영상 생성 완료: {skeleton_video_path}")
            
            # 아이 시퀀스를 query로 사용 (없으면 부모 시퀀스)
            child_seq = norm_result.get("child_sequence")
            parent_seq = norm_result.get("parent_sequence")
            
            # 부모 시퀀스 필수 체크
            if parent_seq is None:
                raise PipelineError(
                    message="부모 시퀀스를 감지하지 못했습니다. 부모와 아이가 함께 있는 영상이 필요합니다.",
                    code="PARENT_NOT_DETECTED",
                    details={"video_path": video_path}
                )
            
            # 아이 시퀀스 필수 체크
            if child_seq is None:
                raise PipelineError(
                    message="아이 시퀀스를 감지하지 못했습니다. 부모와 아이가 함께 있는 영상이 필요합니다.",
                    code="CHILD_NOT_DETECTED",
                    details={"video_path": video_path}
                )
            
            # 부모-아이 분석 진행
            query_normalized = child_seq
            ref_normalized = parent_seq
            logger.info("부모-아이 시퀀스 분석 시작")
            
            # 7. 반응 지연 계산 (DTW 정렬 전 - 부모-아이 상대 시간)
            threshold = settings.get_action_threshold(action_type)
            reaction_delay_detail = None
            
            # 부모-아이 모두 감지됨 → 상대 반응 지연 계산
            reaction_delay, reaction_delay_detail = self._calculate_reaction_delay_from_parent(
                parent_sequence=parent_seq,
                child_sequence=child_seq,
                ref_sequence=parent_seq,  # 부모 시퀀스를 참조로 사용
                fps=video_info.fps,
                threshold=threshold,
                action_type=action_type
            )
            
            # 8. DTW ALIGNMENT
            logger.info("시간 정렬 중...")
            aligned_query, aligned_ref = self.dtw_aligner.align_sequences(
                query_normalized, ref_normalized
            )
            
            # 9. SIMILARITY CALCULATION
            logger.info("유사도 계산 중...")
            similarity_result = self.similarity_calculator.compute_similarity(
                aligned_query, aligned_ref, aligned=True
            )
            
            # 10. 지속 시간 계산 (정렬 후 유사도 기반)
            duration = self._calculate_duration(
                similarity_result.frame_similarities,
                video_info.fps,
                threshold=threshold
            )
            
            validity = self._calculate_validity(query_normalized)
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # role_info에 반응 지연 상세 정보 추가
            if role_info and reaction_delay_detail:
                role_info["reaction_delay_detail"] = reaction_delay_detail
            
            # 시각화 정보 구성
            visualization_info = {
                "frames_folder": str(frames_folder),
                "visualized_folder": str(viz_folder),
                "skeleton_video": str(skeleton_video_path) if skeleton_video_path else None,
                "extracted_frames": extraction_result.saved_count,
                "visualized_frames": viz_count,
                "valid_pose_frames": valid_count,
                "role_based_visualization": identify_roles
            }
            
            result = AnalysisResult(
                passed=similarity_result.overall >= threshold,
                similarity_score=similarity_result.overall,
                reaction_delay_sec=reaction_delay,
                duration_sec=duration,
                validity=validity,
                threshold_used=threshold,
                action_type=action_type,
                age_months=age_months,
                processing_time_sec=processing_time,
                role_info=role_info,
                details={
                    "upper_body_score": similarity_result.upper_body,
                    "lower_body_score": similarity_result.lower_body,
                    "head_score": similarity_result.head,
                    "total_frames_analyzed": len(frames_data),
                    "valid_frame_ratio": similarity_result.valid_frame_ratio,
                    "video_duration_sec": video_info.duration_sec,
                    "video_fps": video_info.fps,
                    "use_parent_reference": use_parent_reference,
                    "smooth_method": smooth_method if smooth else None
                },
                visualization_info=visualization_info
            )
            
            logger.info(
                f"분석 완료: pass={result.passed}, "
                f"score={result.similarity_score:.4f}, "
                f"time={processing_time:.2f}s"
            )
            
            return result
            
        except PipelineError:
            raise
        except Exception as e:
            logger.error(f"분석 중 예외 발생: {e}", exc_info=True)
            raise PipelineError(
                message=f"분석 중 오류 발생: {str(e)}",
                code="ANALYSIS_ERROR",
                details={"video_path": video_path, "action_type": action_type}
            )
    
    def _visualize_frames(
        self,
        frames_folder: Path,
        frames_data: list,
        output_folder: Path
    ) -> int:
        """
        프레임에 스켈레톤을 그려서 저장.
        
        Args:
            frames_folder: 원본 프레임 폴더
            frames_data: PoseExtractor 결과
            output_folder: 시각화 출력 폴더
            
        Returns:
            시각화된 프레임 수
        """
        from PIL import Image
        from app.utils.visualize import draw_skeleton
        
        visualized_count = 0
        
        for frame_data in frames_data:
            frame_idx = frame_data.frame_idx
            image_path = frames_folder / f"frame_{frame_idx:05d}.jpg"
            
            if not image_path.exists():
                continue
            
            # 이미지 로드
            image = Image.open(image_path)
            
            # 스켈레톤 그리기
            if frame_data.is_valid and frame_data.persons:
                results = []
                for person in frame_data.persons:
                    keypoints_list = [
                        {"name": name, "x": kp["x"], "y": kp["y"], "score": kp["score"]}
                        for name, kp in person.keypoints.items()
                    ]
                    results.append({
                        "person_id": person.person_id,
                        "bbox": person.bbox,
                        "keypoints": keypoints_list
                    })
                image = draw_skeleton(image, results)
            
            # 저장
            output_path = output_folder / VISUALIZED_FILENAME_PATTERN.format(frame_idx)
            image.save(output_path)
            visualized_count += 1
        
        return visualized_count
    
    def _visualize_frames_with_roles(
        self,
        frames_folder: Path,
        frames_data: list,
        output_folder: Path,
        frame_persons: Optional[list] = None
    ) -> int:
        """
        프레임에 역할 기반 색상으로 스켈레톤을 그려서 저장.
        
        부모: 파란색, 아이: 주황색으로 구분하여 시각화합니다.
        
        Args:
            frames_folder: 원본 프레임 폴더
            frames_data: PoseExtractor 결과
            output_folder: 시각화 출력 폴더
            frame_persons: 역할 식별 결과 (FramePersons 리스트)
            
        Returns:
            시각화된 프레임 수
        """
        from PIL import Image
        from app.utils.visualize import draw_multi_person_skeleton, draw_skeleton
        
        visualized_count = 0
        
        # frame_persons를 인덱스로 빠르게 접근하기 위한 딕셔너리
        frame_persons_dict = {}
        if frame_persons:
            for fp in frame_persons:
                frame_persons_dict[fp.frame_idx] = fp
        
        for frame_data in frames_data:
            frame_idx = frame_data.frame_idx
            image_path = frames_folder / FRAME_FILENAME_PATTERN.format(frame_idx)
            
            if not image_path.exists():
                continue
            
            # 이미지 로드
            image = Image.open(image_path)
            
            if frame_data.is_valid and frame_data.persons:
                # 역할 정보가 있으면 역할 기반 시각화
                if frame_idx in frame_persons_dict:
                    fp = frame_persons_dict[frame_idx]
                    
                    # FramePersons에서 부모/아이 데이터 추출
                    # IdentifiedPerson.person_pose.keypoints로 접근
                    parent_results = None
                    child_results = None
                    
                    if fp.parent and fp.parent.person_pose and fp.parent.person_pose.keypoints:
                        parent_kp = fp.parent.person_pose.keypoints
                        parent_bbox = fp.parent.person_pose.bbox if fp.parent.person_pose.bbox else [0, 0, 0, 0]
                        parent_results = [{
                            "person_id": 0,
                            "bbox": parent_bbox,
                            "keypoints": [
                                {"name": name, "x": kp["x"], "y": kp["y"], "score": kp["score"]}
                                for name, kp in parent_kp.items()
                            ]
                        }]
                    
                    if fp.child and fp.child.person_pose and fp.child.person_pose.keypoints:
                        child_kp = fp.child.person_pose.keypoints
                        child_bbox = fp.child.person_pose.bbox if fp.child.person_pose.bbox else [0, 0, 0, 0]
                        child_results = [{
                            "person_id": 1,
                            "bbox": child_bbox,
                            "keypoints": [
                                {"name": name, "x": kp["x"], "y": kp["y"], "score": kp["score"]}
                                for name, kp in child_kp.items()
                            ]
                        }]
                    
                    image = draw_multi_person_skeleton(
                        image, 
                        parent_results=parent_results, 
                        child_results=child_results
                    )
                else:
                    # 역할 정보 없으면 기본 시각화
                    results = []
                    for person in frame_data.persons:
                        keypoints_list = [
                            {"name": name, "x": kp["x"], "y": kp["y"], "score": kp["score"]}
                            for name, kp in person.keypoints.items()
                        ]
                        results.append({
                            "person_id": person.person_id,
                            "bbox": person.bbox,
                            "keypoints": keypoints_list
                        })
                    image = draw_skeleton(image, results)
            
            # 저장
            out_path = output_folder / VISUALIZED_FILENAME_PATTERN.format(frame_idx)
            image.save(out_path)
            visualized_count += 1
        
        return visualized_count
    
    def _create_skeleton_video(
        self,
        frames_folder: Path,
        output_path: Path,
        fps: float = 10.0
    ) -> None:
        """
        시각화된 프레임들을 동영상으로 합성.
        
        Args:
            frames_folder: 시각화된 프레임 폴더
            output_path: 출력 동영상 경로
            fps: 동영상 FPS
        """
        import cv2
        
        frame_files = sorted(frames_folder.glob(f"viz_*{IMAGE_EXTENSION}"))
        
        if not frame_files:
            logger.warning("시각화된 프레임이 없습니다.")
            return
        
        # 첫 프레임으로 크기 확인
        first_frame = cv2.imread(str(frame_files[0]))
        height, width = first_frame.shape[:2]
        
        # 비디오 라이터
        fourcc = cv2.VideoWriter_fourcc(*VIDEO_FOURCC)
        out = cv2.VideoWriter(str(output_path), fourcc, fps, (width, height))
        
        for frame_path in frame_files:
            frame = cv2.imread(str(frame_path))
            out.write(frame)
        
        out.release()
        logger.debug(f"동영상 생성: {output_path} ({len(frame_files)} frames, {fps}fps)")


def main():
    """
    CLI 실행 진입점.
    
    사용법:
        python -m app.pipeline.analyzer <video_path> <action_type> [options]
        
    예시:
        python -m app.pipeline.analyzer video.mp4 clapping --age 24
        python -m app.pipeline.analyzer video.mp4 hurray --age 18 --visualize
        python -m app.pipeline.analyzer video.mp4 clapping --visualize --output results/
    """
    import argparse
    import sys
    
    parser = argparse.ArgumentParser(
        description="동작 모방행동 분석 CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예시:
  python -m app.pipeline.analyzer video.mp4 clapping --age 24
  python -m app.pipeline.analyzer video.mp4 hurray --age 18 --visualize
  python -m app.pipeline.analyzer video.mp4 clapping -v -o results/
        """
    )
    
    parser.add_argument(
        "video_path",
        help="분석할 영상 파일 경로"
    )
    parser.add_argument(
        "action_type",
        choices=MotionAnalyzer.SUPPORTED_ACTIONS,
        help=f"동작 유형 ({', '.join(MotionAnalyzer.SUPPORTED_ACTIONS)})"
    )
    parser.add_argument(
        "--age", "-a",
        type=int,
        default=18,
        help="아동 월령 (기본: 18)"
    )
    parser.add_argument(
        "--visualize", "-v",
        action="store_true",
        help="스켈레톤 시각화 활성화"
    )
    parser.add_argument(
        "--output", "-o",
        default="analysis_output",
        help="시각화 출력 폴더 (기본: analysis_output)"
    )
    parser.add_argument(
        "--no-video",
        action="store_true",
        help="스켈레톤 동영상 생성 안함"
    )
    parser.add_argument(
        "--no-parent-ref",
        action="store_true",
        help="부모 시퀀스 참조 비활성화 (기본 참조 동작 사용)"
    )
    parser.add_argument(
        "--no-role-identify",
        action="store_true",
        help="부모/아이 역할 식별 비활성화"
    )
    parser.add_argument(
        "--no-smooth",
        action="store_true",
        help="스무딩 비활성화"
    )
    parser.add_argument(
        "--smooth-method",
        choices=["one_euro", "ema", "moving_average"],
        default="one_euro",
        help="스무딩 방법 (기본: one_euro)"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="상세 로그 출력"
    )
    
    args = parser.parse_args()
    
    # 로깅 설정
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # 영상 파일 확인
    if not Path(args.video_path).exists():
        print(f"😭 영상 파일을 찾을 수 없습니다: {args.video_path}")
        sys.exit(1)
    
    print("\n" + "=" * 60)
    print("👶 동작 모방행동 분석기")
    print("=" * 60)
    print(f"  영상: {args.video_path}")
    print(f"  동작: {args.action_type}")
    print(f"  월령: {args.age}개월")
    print(f"  시각화: {'⭕ 활성화' if args.visualize else '✖️ 비활성화'}")
    print(f"  부모 참조: {'✖️ 비활성화' if args.no_parent_ref else '⭕ 활성화 (기본)'}")
    print(f"  역할 식별: {'✖️ 비활성화' if args.no_role_identify else '⭕ 활성화'}")
    print(f"  스무딩: {'✖️ 비활성화' if args.no_smooth else f'⭕ {args.smooth_method}'}")
    if args.visualize:
        print(f"  출력 폴더: {args.output}")
        print(f"  동영상 생성: {'✖️ 비활성화' if args.no_video else '⭕ 활성화'}")
    print("=" * 60 + "\n")
    
    # Analyzer 초기화
    analyzer = MotionAnalyzer(use_folder_mode=True)
    
    try:
        if args.visualize:
            # 시각화 포함 분석
            result = analyzer.analyze_with_visualization(
                video_path=args.video_path,
                action_type=args.action_type,
                age_months=args.age,
                output_folder=args.output,
                save_skeleton_video=not args.no_video,
                use_parent_reference=not args.no_parent_ref,
                identify_roles=not args.no_role_identify,
                smooth=not args.no_smooth,
                smooth_method=args.smooth_method
            )
        else:
            # 기본 분석
            result = analyzer.analyze(
                video_path=args.video_path,
                action_type=args.action_type,
                age_months=args.age,
                use_parent_reference=not args.no_parent_ref,
                identify_roles=not args.no_role_identify,
                smooth=not args.no_smooth,
                smooth_method=args.smooth_method
            )
        
        # 결과 출력
        print("\n" + "=" * 60)
        print("👶 분석 결과")
        print("=" * 60)
        print(f"  통과 여부: {'👶 PASS' if result.passed else '😭 FAIL'}")
        print(f"  유사도 점수: {result.similarity_score:.2%}")
        print(f"  적용 기준: {result.threshold_used:.2%}")
        print(f"  반응 지연: {result.reaction_delay_sec:.2f}초")
        print(f"  동작 지속: {result.duration_sec:.2f}초")
        print(f"  분석 유효성: {result.validity:.2%}")
        print(f"  처리 시간: {result.processing_time_sec:.2f}초")
        
        print("\n👶 상세 정보:")
        print(f"  상체 점수: {result.details['upper_body_score']:.2%}")
        print(f"  하체 점수: {result.details['lower_body_score']:.2%}")
        print(f"  머리 점수: {result.details['head_score']:.2%}")
        print(f"  분석 프레임: {result.details['total_frames_analyzed']}개")
        print(f"  유효 프레임 비율: {result.details['valid_frame_ratio']:.2%}")
        
        if result.role_info:
            print("\n👶 역할 식별 정보:")
            print(f"  부모 감지: {'👶' if result.role_info['parent_identified'] else '😭'}")
            print(f"  아이 감지: {'👶' if result.role_info['child_identified'] else '😭'}")
            if result.role_info['parent_torso_length']:
                print(f"  부모 몸통 길이: {result.role_info['parent_torso_length']:.1f}px")
            if result.role_info['child_torso_length']:
                print(f"  아이 몸통 길이: {result.role_info['child_torso_length']:.1f}px")
            
            # 반응 지연 상세 정보 출력
            if result.role_info.get('reaction_delay_detail'):
                detail = result.role_info['reaction_delay_detail']
                print("\n👶 반응 지연 상세:")
                print(f"  부모 동작 시작: 프레임 {detail['parent_start_frame']} ({detail['parent_start_sec']:.2f}초)")
                print(f"  아이 동작 시작: 프레임 {detail['child_start_frame']} ({detail['child_start_sec']:.2f}초)")
                print(f"  지연 프레임: {detail['delay_frames']}프레임")
        
        if result.visualization_info:
            print("\n👶 시각화 정보:")
            print(f"  프레임 폴더: {result.visualization_info['frames_folder']}")
            print(f"  시각화 폴더: {result.visualization_info['visualized_folder']}")
            if result.visualization_info.get('skeleton_video'):
                print(f"  스켈레톤 동영상: {result.visualization_info['skeleton_video']}")
            print(f"  추출 프레임: {result.visualization_info['extracted_frames']}개")
            print(f"  시각화 프레임: {result.visualization_info['visualized_frames']}개")
            print(f"  유효 자세 프레임: {result.visualization_info['valid_pose_frames']}개")
            if result.visualization_info.get('role_based_visualization'):
                print("  역할 기반 색상: 👶 활성화 (부모=파란색, 아이=주황색)")
        
        print("\n" + "=" * 60)
        print("👶 분석 완료!")
        print("=" * 60 + "\n")
        
    except Exception as e:
        print(f"\n✖️ 분석 실패: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()