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

from app.config import settings, EmotionConfig
from app.pipeline.video_processor import VideoProcessor
from app.pipeline.pose_extractor import PoseExtractor
from app.pipeline.normalizer import PoseNormalizer
from app.pipeline.dtw import DTWAligner
from app.pipeline.similarity import SimilarityCalculator, ActionWeightPresets
from app.pipeline.exceptions import (
    PipelineError,
    InvalidInputError
)

# 표정 분석 모듈 (Lazy Loading)
_expression_analyzer = None

def _get_expression_analyzer():
    """ExpressionAnalyzer 지연 로딩"""
    global _expression_analyzer
    if _expression_analyzer is None:
        try:
            from app.pipeline.emotion import ExpressionAnalyzer
            _expression_analyzer = ExpressionAnalyzer(EmotionConfig())
            logger.info("✅ ExpressionAnalyzer 로드 성공")
        except Exception as e:
            logger.warning(f"⚠️ ExpressionAnalyzer 로드 실패: {e}")
            _expression_analyzer = None
    return _expression_analyzer

logger = logging.getLogger(__name__)


# ==================== 상수 정의 ====================
# 동작 감지 결과
ACTION_NOT_DETECTED = -1  # 동작 미감지 시 반환값

# 반응 지연 및 지속 시간 계산
DEFAULT_REACTION_DELAY_THRESHOLD = 0.85  # 동작 시작 판정 기본 임계값
DEFAULT_DURATION_THRESHOLD = 0.8  # 동작 지속 판정 기본 임계값

# 유사도 계산
EPSILON_NORM_CHECK = 1e-8  # 정규화 벡터 크기 체크용 엡실론

# 만세 동작 감지
HURRAY_WRIST_MARGIN = 0.3  # 손목이 어깨 위로 올라가야 하는 거리 (정규화 좌표)

# 박수 동작 감지
CLAPPING_WRIST_DISTANCE_CLOSE = 0.2  # 손목이 가까워졌다고 판단하는 거리
CLAPPING_WRIST_DISTANCE_FAR = 0.4  # 손목이 벌어졌다고 판단하는 거리
CLAPPING_MIN_DISTANCE_CHANGE = 0.15  # 최소 거리 변화량 (박수 여부 판단)

# 점프 동작 감지
JUMPING_HIP_RISE_MARGIN = 0.03  # 엉덩이 상승 마진

# 발차기 동작 감지
KICKING_ANKLE_HEIGHT_DIFF = 0.2  # 발목 높이 차이

# 던지기 동작 감지
THROWING_WRIST_ABOVE_SHOULDER = 0.1  # 손목이 어깨 위로

# 뒤로 걷기 동작 감지
WALKING_BACK_MOVE_THRESHOLD = 0.05  # 이동 감지 임계값

# 개선된 유사도 기반 감지 (fallback)
SIMILARITY_WINDOW_SIZE = 5  # 슬라이딩 윈도우 크기
INITIAL_FRAMES_TO_SKIP = 3  # 준비 자세로 간주할 초기 프레임 수
SIMILARITY_CHANGE_THRESHOLD = 0.1  # 유사도 변화율 임계값

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
class TrialResult:
    """
    단일 시도(trial) 결과 데이터.
    
    Attributes:
        trial_index: 시도 번호 (1, 2, 3)
        action_type: 동작 유형
        success: 성공 여부
        similarity_score: 동작 유사도 (0.0 ~ 1.0)
        parent_start_time: 부모 동작 시작 시간 (초)
        parent_end_time: 부모 동작 종료 시간 (초)
        child_start_time: 아이 동작 시작 시간 (초, None일 수 있음)
        child_end_time: 아이 동작 종료 시간 (초, None일 수 있음)
        latency_s: 부모 종료 → 아이 시작 반응 지연 시간 (초, None일 수 있음)
        duration_s: 아이 동작 지속 시간 (초, None일 수 있음)
        attention_ratio: 주의/상호작용 유효성 (0.0 ~ 1.0)
    """
    trial_index: int
    action_type: str
    success: bool
    similarity_score: float
    parent_start_time: float
    parent_end_time: float
    child_start_time: Optional[float]
    child_end_time: Optional[float]
    latency_s: Optional[float]
    duration_s: Optional[float]
    attention_ratio: float
    
    def to_dict(self) -> dict[str, Any]:
        """딕셔너리로 변환"""
        result = {
            "trial_index": self.trial_index,
            "action_type": self.action_type,
            "success": bool(self.success),
            "similarity_score": float(round(self.similarity_score, 4)),
            "parent_start_time": float(round(self.parent_start_time, 2)),
            "parent_end_time": float(round(self.parent_end_time, 2)),
            "child_start_time": float(round(self.child_start_time, 2)) if self.child_start_time is not None else None,
            "child_end_time": float(round(self.child_end_time, 2)) if self.child_end_time is not None else None,
            "latency_s": float(round(self.latency_s, 2)) if self.latency_s is not None else None,
            "duration_s": float(round(self.duration_s, 2)) if self.duration_s is not None else None,
            "attention_ratio": float(round(self.attention_ratio, 4))
        }
        return result


@dataclass
class MultiTrialAnalysisResult:
    """
    다중 시도 분석 결과 (pose_imitation).
    
    Attributes:
        assessment_type: 평가 유형 ("pose_imitation")
        age_months: 아동 월령
        processing_time_sec: 전체 처리 소요 시간
        metrics: 시도별 결과 리스트
        ados: ADOS 평가 점수 (B6: 즐거움 감지, A8: 주의/반응, B18: 사회적 모방)
        role_info: 부모/아이 역할 정보
        details: 상세 분석 정보
    """
    assessment_type: str  # "pose_imitation"
    age_months: int
    processing_time_sec: float
    metrics: dict[str, list[dict[str, Any]]]  # {"per_trial": [...]}
    ados: dict[str, Any]  # {"B6": bool, "A8": int, "B18": bool}
    role_info: Optional[dict[str, Any]] = field(default=None)
    details: dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            "assessment_type": self.assessment_type,
            "age_months": int(self.age_months),
            "processing_time_sec": float(round(self.processing_time_sec, 2)),
            "metrics": self.metrics,
            "ados": self.ados,
            "role_info": self.role_info,
            "details": self.details
        }


@dataclass
class PoseImitationResponse:
    """
    RabbitMQ 응답용 간결한 데이터 구조.
    
    Attributes:
        request_id: 요청 고유 ID (UUID)
        analyzed_at: 분석 완료 시각 (ISO 8601, KST)
        status: 분석 상태 ("completed" | "failed")
        metrics: per_trial 리스트
        ados: ADOS 평가 점수
    """
    request_id: str
    analyzed_at: str  # ISO 8601 형식 (KST)
    status: str  # "completed" | "failed"
    metrics: dict[str, list[dict[str, Any]]]  # {"per_trial": [...]}
    ados: dict[str, Any]  # {"B6": bool, "A8": int, "B18": bool}
    
    def to_dict(self) -> dict[str, Any]:
        """RabbitMQ 응답용 딕셔너리로 변환"""
        return {
            "request_id": self.request_id,
            "analyzed_at": self.analyzed_at,
            "status": self.status,
            "metrics": self.metrics,
            "ADOS": self.ados  # 대문자 키
        }


@dataclass
class AnalysisResult:
    """
    분석 결과 데이터.
    
    Attributes:
        passed: 통과 여부
        similarity_score: 전체 유사도 점수
        reaction_delay_sec: 반응 지연 시간 (초), 미감지 시 None
        duration_sec: 동작 수행 시간 (초), 미감지 시 None
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
    reaction_delay_sec: Optional[float]  # 아이 동작 미감지 시 None
    duration_sec: Optional[float]  # 아이 동작 미감지 시 None
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
        # reaction_delay_sec, duration_sec는 None일 수 있음 (아이 동작 미감지 시)
        if result["reaction_delay_sec"] is not None:
            result["reaction_delay_sec"] = float(round(result["reaction_delay_sec"], 2))
        if result["duration_sec"] is not None:
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
        
        # 표정 분석기 초기화 (Lazy Loading)
        self.expression_analyzer = _get_expression_analyzer()
        
        logger.info(
            f"MotionAnalyzer 초기화 완료. "
            f"모드: {'폴더 저장' if use_folder_mode else 'Generator'}, "
            f"표정분석: {'✅' if self.expression_analyzer and self.expression_analyzer.available else '❌'}"
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
        smooth_method: str = "one_euro",
        start_sec: float = 0.0,
        end_sec: Optional[float] = None
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
                
                is_segment = start_sec > 0.0 or end_sec is not None
                extraction_result = self.video_processor.extract_frames_to_folder(
                    video_path,
                    output_folder=output_folder,
                    start_sec=start_sec,
                    end_sec=end_sec,
                    validate=not is_segment,
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
                frames = self.video_processor.extract_frames(
                    video_path,
                    start_sec=start_sec,
                    end_sec=end_sec,
                )
                
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
                aligned_query, aligned_ref, aligned=True, action_type=action_type
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
            
            # 아이 동작 감지 여부 확인 (reaction_delay_detail에서)
            child_action_detected = (
                reaction_delay_detail is not None and 
                reaction_delay_detail.get("child_detected", False)
            )
            parent_action_detected = (
                reaction_delay_detail is not None and 
                reaction_delay_detail.get("parent_detected", False)
            )
            
            # passed 판정: 아이 동작 감지 + 유사도 임계값 통과 모두 필요
            if not child_action_detected:
                passed = False
                fail_reason = "child_action_not_detected"
            elif not parent_action_detected:
                passed = False
                fail_reason = "parent_action_not_detected"
            else:
                passed = similarity_result.overall >= threshold
                fail_reason = None if passed else "similarity_below_threshold"
            
            result = AnalysisResult(
                passed=passed,
                similarity_score=similarity_result.overall,
                reaction_delay_sec=reaction_delay,
                duration_sec=duration if child_action_detected else None,
                validity=validity,
                threshold_used=threshold,
                action_type=action_type,
                age_months=age_months,
                processing_time_sec=processing_time,
                role_info=role_info,
                details={
                    "fail_reason": fail_reason,
                    "child_action_detected": child_action_detected,
                    "parent_action_detected": parent_action_detected,
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
        시퀀스에서 동작이 시작되는 프레임 인덱스 감지 (하이브리드 방식).
        
        동작 타입에 따라 특화된 감지 알고리즘을 사용하고,
        미정의 동작은 개선된 유사도 기반으로 감지합니다.
        
        Args:
            sequence: 분석할 시퀀스 (T, 17, 3)
            ref_sequence: 참조 동작 시퀀스 (T_ref, 17, 3)
            threshold: 동작 시작 판정 임계값
            action_type: 동작 타입
            
        Returns:
            동작 시작 프레임 인덱스. 동작 미감지 시 ACTION_NOT_DETECTED(-1) 반환.
        """
        # 특화 알고리즘 매핑
        specialized_detectors = {
            "hurray": self._detect_hurray_start_frame,
            "clapping": self._detect_clapping_start_frame,
            "jumping": self._detect_jumping_start_frame,
            "kicking": self._detect_kicking_start_frame,
            "throwing": self._detect_throwing_start_frame,
            "walking_back": self._detect_walking_back_start_frame,
        }
        
        if action_type in specialized_detectors:
            return specialized_detectors[action_type](sequence)
        else:
            # 미정의 동작: 개선된 유사도 기반 감지
            return self._detect_by_similarity_improved(sequence, ref_sequence, threshold)
    
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
        
        return ACTION_NOT_DETECTED  # 동작 미감지
    
    def _detect_clapping_start_frame(
        self,
        sequence: np.ndarray,
        close_threshold: float = CLAPPING_WRIST_DISTANCE_CLOSE,
        min_change: float = CLAPPING_MIN_DISTANCE_CHANGE
    ) -> int:
        """
        박수 동작 시작 프레임 감지 (손목 거리 변화 기반).
        
        단순히 손목이 가까운 것이 아니라, 손목 간 거리가 
        벌어졌다가 가까워지는 "움직임"을 감지합니다.
        
        Args:
            sequence: 분석할 시퀀스 (T, 17, 3)
            close_threshold: 손목이 가까워졌다고 판단하는 거리
            min_change: 박수로 인정할 최소 거리 변화량
            
        Returns:
            박수 시작 프레임 인덱스. 미감지 시 ACTION_NOT_DETECTED(-1) 반환.
        """
        # COCO: 9=L_Wrist, 10=R_Wrist
        if len(sequence) < 3:
            return ACTION_NOT_DETECTED
        
        # 각 프레임별 손목 거리 계산
        distances = []
        for frame in sequence:
            l_wrist = frame[9, :2]
            r_wrist = frame[10, :2]
            distance = np.linalg.norm(l_wrist - r_wrist)
            distances.append(distance)
        
        # 초기 거리 (준비 자세)
        initial_distance = np.mean(distances[:3])
        
        # 손목이 가까워지면서 거리 변화가 충분한 첫 프레임 찾기
        for i in range(3, len(sequence)):
            current_distance = distances[i]
            distance_change = initial_distance - current_distance
            
            # 손목이 가까워지고, 거리 변화가 충분하면 박수 시작
            if current_distance < close_threshold and distance_change > min_change:
                return i
        
        return ACTION_NOT_DETECTED  # 동작 미감지
    
    def _detect_jumping_start_frame(
        self,
        sequence: np.ndarray,
        margin: float = JUMPING_HIP_RISE_MARGIN
    ) -> int:
        """
        점프 동작 시작 프레임 감지 (발목 + 엉덩이 위치 기반).
        
        발목이나 엉덩이가 초기 위치보다 올라가는 첫 프레임을 감지합니다.
        
        Args:
            sequence: 분석할 시퀀스 (T, 17, 3)
            margin: 상승 마진
            
        Returns:
            점프 시작 프레임 인덱스. 미감지 시 ACTION_NOT_DETECTED(-1) 반환.
        """
        if len(sequence) < 5:
            return ACTION_NOT_DETECTED
        
        # COCO: 11=L_Hip, 12=R_Hip, 15=L_Ankle, 16=R_Ankle
        # 초기 3~5프레임의 평균을 baseline으로 사용
        baseline_frames = min(5, len(sequence) // 3)
        baseline_hip_ys = []
        baseline_ankle_ys = []
        
        for i in range(baseline_frames):
            # 엉덩이
            if sequence[i, 11, 2] > 0.3 and sequence[i, 12, 2] > 0.3:
                hip_y = (sequence[i, 11, 1] + sequence[i, 12, 1]) / 2
                baseline_hip_ys.append(hip_y)
            
            # 발목
            if sequence[i, 15, 2] > 0.3 and sequence[i, 16, 2] > 0.3:
                ankle_y = (sequence[i, 15, 1] + sequence[i, 16, 1]) / 2
                baseline_ankle_ys.append(ankle_y)
        
        if not baseline_hip_ys and not baseline_ankle_ys:
            return ACTION_NOT_DETECTED
        
        baseline_hip_y = np.mean(baseline_hip_ys) if baseline_hip_ys else None
        baseline_ankle_y = np.mean(baseline_ankle_ys) if baseline_ankle_ys else None
        
        # baseline 이후부터 검사
        for i in range(baseline_frames, len(sequence)):
            detected = False
            
            # 발목 체크 (더 민감함 - 발이 땅에서 떨어지는 것 감지)
            if baseline_ankle_y is not None:
                if sequence[i, 15, 2] > 0.3 and sequence[i, 16, 2] > 0.3:
                    current_ankle_y = (sequence[i, 15, 1] + sequence[i, 16, 1]) / 2
                    # 발목이 baseline보다 margin 이상 올라갔으면
                    if current_ankle_y < (baseline_ankle_y - margin):
                        logger.debug(f"점프 감지(발목): frame={i}, baseline_y={baseline_ankle_y:.3f}, current_y={current_ankle_y:.3f}, diff={baseline_ankle_y - current_ankle_y:.3f}")
                        detected = True
            
            # 엉덩이 체크 (보조 수단)
            if not detected and baseline_hip_y is not None:
                if sequence[i, 11, 2] > 0.3 and sequence[i, 12, 2] > 0.3:
                    current_hip_y = (sequence[i, 11, 1] + sequence[i, 12, 1]) / 2
                    # 엉덩이가 baseline보다 margin 이상 올라갔으면
                    if current_hip_y < (baseline_hip_y - margin):
                        logger.debug(f"점프 감지(엉덩이): frame={i}, baseline_y={baseline_hip_y:.3f}, current_y={current_hip_y:.3f}, diff={baseline_hip_y - current_hip_y:.3f}")
                        detected = True
            
            if detected:
                return i
        
        logger.debug(f"점프 미감지: hip_baseline={baseline_hip_y:.3f if baseline_hip_y else 'N/A'}, ankle_baseline={baseline_ankle_y:.3f if baseline_ankle_y else 'N/A'}, margin={margin}")
        return ACTION_NOT_DETECTED  # 동작 미감지
    
    def _detect_kicking_start_frame(
        self,
        sequence: np.ndarray,
        height_diff: float = KICKING_ANKLE_HEIGHT_DIFF
    ) -> int:
        """
        발차기 동작 시작 프레임 감지 (발목 높이 기반).
        
        한쪽 발목이 반대쪽보다 높이 올라가는 첫 프레임을 감지합니다.
        무릎 꿇은 상태의 미세한 움직임을 피하기 위해 임계값을 높게 설정.
        
        Args:
            sequence: 분석할 시퀀스 (T, 17, 3)
            height_diff: 발목 높이 차이 임계값
            
        Returns:
            발차기 시작 프레임 인덱스. 미감지 시 ACTION_NOT_DETECTED(-1) 반환.
        """
        # COCO: 15=L_Ankle, 16=R_Ankle
        strict_threshold = height_diff * 1.3
        
        for i, frame in enumerate(sequence):
            # 신뢰도 체크
            if frame[15, 2] < 0.3 or frame[16, 2] < 0.3:
                continue
                
            l_ankle_y = frame[15, 1]
            r_ankle_y = frame[16, 1]
            
            # 둘 중 하나가 다른 쪽보다 strict_threshold 이상 위에 있으면
            ankle_diff = abs(l_ankle_y - r_ankle_y)
            if ankle_diff > strict_threshold:
                logger.debug(f"발차기 감지: frame={i}, ankle_diff={ankle_diff:.3f}, threshold={strict_threshold:.3f}")
                return i
        
        logger.debug(f"발차기 미감지: threshold={strict_threshold:.3f}")
        return ACTION_NOT_DETECTED  # 동작 미감지
    
    def _detect_throwing_start_frame(
        self,
        sequence: np.ndarray,
        margin: float = THROWING_WRIST_ABOVE_SHOULDER
    ) -> int:
        """
        던지기 동작 시작 프레임 감지 (손목 위치 기반).
        
        한쪽 손목이 어깨 위로 올라가는 첫 프레임(백스윙)을 감지합니다.
        
        Args:
            sequence: 분석할 시퀀스 (T, 17, 3)
            margin: 손목이 어깨 위로 올라가야 하는 거리
            
        Returns:
            던지기 시작 프레임 인덱스. 미감지 시 ACTION_NOT_DETECTED(-1) 반환.
        """
        # COCO: 5=L_Shoulder, 6=R_Shoulder, 9=L_Wrist, 10=R_Wrist
        for i, frame in enumerate(sequence):
            # 왼손 또는 오른손 중 하나가 어깨 위로
            l_above = frame[9, 1] < (frame[5, 1] - margin)
            r_above = frame[10, 1] < (frame[6, 1] - margin)
            if l_above or r_above:
                return i
        return ACTION_NOT_DETECTED  # 동작 미감지
    
    def _detect_walking_back_start_frame(
        self,
        sequence: np.ndarray,
        move_threshold: float = WALKING_BACK_MOVE_THRESHOLD
    ) -> int:
        """
        뒤로 걷기 동작 시작 프레임 감지 (중심 이동 기반).
        
        전체 중심점(골반)이 초기 대비 이동하는 첫 프레임을 감지합니다.
        
        Args:
            sequence: 분석할 시퀀스 (T, 17, 3)
            move_threshold: 이동 감지 임계값
            
        Returns:
            걷기 시작 프레임 인덱스. 미감지 시 ACTION_NOT_DETECTED(-1) 반환.
        """
        # COCO: 11=L_Hip, 12=R_Hip (골반 중심 사용)
        initial_hip_x = (sequence[0, 11, 0] + sequence[0, 12, 0]) / 2
        
        for i, frame in enumerate(sequence):
            current_hip_x = (frame[11, 0] + frame[12, 0]) / 2
            if abs(current_hip_x - initial_hip_x) > move_threshold:
                return i
        return ACTION_NOT_DETECTED  # 동작 미감지
    
    def _detect_by_similarity_improved(
        self,
        sequence: np.ndarray,
        ref_sequence: np.ndarray,
        threshold: float
    ) -> int:
        """
        개선된 유사도 기반 동작 시작 감지 (fallback).
        
        동작 절정 프레임을 찾고, 유사도 변화량으로 동작 시작을 감지합니다.
        
        Args:
            sequence: 분석할 시퀀스 (T, 17, 3)
            ref_sequence: 참조 동작 시퀀스 (T_ref, 17, 3)
            threshold: 동작 시작 판정 임계값
            
        Returns:
            동작 시작 프레임 인덱스. 미감지 시 ACTION_NOT_DETECTED(-1) 반환.
        """
        if len(sequence) < INITIAL_FRAMES_TO_SKIP + SIMILARITY_WINDOW_SIZE:
            return ACTION_NOT_DETECTED
        
        # 1. 동작 절정 프레임 찾기 (첫 프레임과 가장 다른 프레임)
        peak_frame = self._find_peak_action_frame(ref_sequence)
        
        # 2. 초기 프레임의 유사도 계산 (baseline)
        initial_sim = self._quick_frame_similarity(sequence[0], peak_frame)
        
        # 3. 슬라이딩 윈도우로 유사도 변화 감지
        for i in range(INITIAL_FRAMES_TO_SKIP, len(sequence) - SIMILARITY_WINDOW_SIZE):
            window_sims = []
            for j in range(SIMILARITY_WINDOW_SIZE):
                sim = self._quick_frame_similarity(sequence[i + j], peak_frame)
                window_sims.append(sim)
            
            avg_sim = np.mean(window_sims)
            sim_change = avg_sim - initial_sim
            
            # 유사도가 초기 대비 크게 변화하면 동작 시작으로 간주
            if sim_change > SIMILARITY_CHANGE_THRESHOLD:
                return i
        
        return ACTION_NOT_DETECTED  # 동작 미감지
    
    def _find_peak_action_frame(self, sequence: np.ndarray) -> np.ndarray:
        """
        시퀀스에서 동작 절정 프레임 찾기.
        
        첫 프레임(준비 자세)과 가장 다른 프레임을 반환합니다.
        
        Args:
            sequence: 시퀀스 (T, 17, 3)
            
        Returns:
            동작 절정 프레임 (17, 3)
        """
        first_frame = sequence[0]
        max_diff = 0
        peak_idx = len(sequence) // 2  # 기본값은 중간
        
        for i, frame in enumerate(sequence):
            diff = np.linalg.norm(frame[:, :2] - first_frame[:, :2])
            if diff > max_diff:
                max_diff = diff
                peak_idx = i
        
        return sequence[peak_idx]
    
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
            - None: 부모 또는 아이 동작이 감지되지 않음
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
        
        # 동작 감지 여부 판단
        parent_detected = parent_start != ACTION_NOT_DETECTED
        child_detected = child_start != ACTION_NOT_DETECTED
        
        # 🔥 중요: 유사도가 높으면 동작 감지로 간주 (기하학적 감지 실패해도 허용)
        # threshold보다 10% 높으면 동작이 있었다고 판단
        high_similarity_detected = False
        if not child_detected or not parent_detected:
            # 유사도 기반 체크 (간단히 프레임별 평균 계산)
            from app.pipeline.similarity import SimilarityCalculator
            temp_calc = SimilarityCalculator()
            
            try:
                # 임시로 유사도 계산해서 확인
                aligned_query, aligned_ref = self.dtw_aligner.align_sequences(
                    child_sequence, ref_sequence
                )
                temp_result = temp_calc.compute_similarity(
                    aligned_query, aligned_ref, aligned=True, action_type=action_type
                )
                
                # 유사도가 threshold + 0.1 이상이면 동작 있음으로 간주
                if temp_result.overall >= (threshold + 0.1):
                    logger.info(
                        f"⚠️ 기하학적 감지 실패했지만 유사도 {temp_result.overall:.1%} >= "
                        f"{threshold + 0.1:.1%}이므로 동작 감지로 간주"
                    )
                    high_similarity_detected = True
                    
                    # 유사도 기반으로 동작 시작 프레임 찾기 (프레임별 유사도가 급증하는 지점)
                    if not child_detected:
                        # 개선된 유사도 기반 감지 사용
                        child_start_alt = self._detect_by_similarity_improved(
                            child_sequence, ref_sequence, threshold * 0.8  # 더 낮은 임계값 사용
                        )
                        if child_start_alt != ACTION_NOT_DETECTED:
                            child_start = child_start_alt
                            child_detected = True
                            logger.info(f"✓ 아이 동작 시작: frame={child_start} (유사도 기반)")
                        else:
                            # 그래도 못 찾으면 중간 지점 사용
                            child_start = len(child_sequence) // 3
                            child_detected = True
                            logger.info(f"✓ 아이 동작 시작: frame={child_start} (추정값, 시퀀스 1/3 지점)")
                    
                    if not parent_detected:
                        # 부모도 유사도 기반으로 찾기
                        parent_start_alt = self._detect_by_similarity_improved(
                            parent_sequence, ref_sequence, threshold * 0.8
                        )
                        if parent_start_alt != ACTION_NOT_DETECTED:
                            parent_start = parent_start_alt
                            parent_detected = True
                            logger.info(f"✓ 부모 동작 시작: frame={parent_start} (유사도 기반)")
                        else:
                            parent_start = len(parent_sequence) // 3
                            parent_detected = True
                            logger.info(f"✓ 부모 동작 시작: frame={parent_start} (추정값, 시퀀스 1/3 지점)")
            except Exception as e:
                logger.warning(f"유사도 기반 동작 감지 실패: {e}")
        
        # 상세 정보
        detail = {
            "parent_start_frame": parent_start if parent_detected else None,
            "parent_start_sec": parent_start / fps if parent_detected else None,
            "child_start_frame": child_start if child_detected else None,
            "child_start_sec": child_start / fps if child_detected else None,
            "parent_detected": parent_detected,
            "child_detected": child_detected,
            "delay_frames": None,
            "detection_method": action_type  # 동작 타입별 특화 알고리즘 명시
        }
        
        # 부모/아이 둘 다 감지된 경우만 지연 계산
        if parent_detected and child_detected:
            delay_frames = child_start - parent_start
            delay_sec = delay_frames / fps
            detail["delay_frames"] = delay_frames
            
            logger.info(
                f"반응 지연 분석: 부모 시작={parent_start}프레임({parent_start/fps:.2f}초), "
                f"아이 시작={child_start}프레임({child_start/fps:.2f}초), "
                f"지연={delay_sec:.2f}초 (방식: {detail['detection_method']})"
            )
            return delay_sec, detail
        
        # 감지 실패 로깅
        if not parent_detected:
            logger.warning(f"부모 동작 미감지 (action_type={action_type})")
        if not child_detected:
            logger.warning(f"아이 동작 미감지 (action_type={action_type})")
        
        return None, detail
    


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
        smooth_method: str = "one_euro",
        start_sec: float = 0.0,
        end_sec: Optional[float] = None
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
            start_sec: 영상 시작 시간 (초, 구간 분할 시 사용)
            end_sec: 영상 종료 시간 (초, None이면 끝까지)

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
            is_segment = start_sec > 0.0 or end_sec is not None
            logger.info(
                f"영상 처리 시작: {video_path}"
                + (f" (구간: {start_sec:.1f}s~{end_sec:.1f}s)"
                   if is_segment and end_sec else "")
            )
            extraction_result = self.video_processor.extract_frames_to_folder(
                video_path,
                output_folder=frames_folder,
                start_sec=start_sec,
                end_sec=end_sec,
                validate=not is_segment,
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
            
            # 6. 반응 지연 계산 (DTW 정렬 전 - 부모-아이 상대 시간)
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
            
            # 아이 동작 미감지 체크
            child_action_detected = reaction_delay_detail.get("child_detected", False)
            parent_action_detected = reaction_delay_detail.get("parent_detected", False)
            
            # 부모/아이 동작 미감지 시 경고만 출력 (시각화는 계속 진행)
            if not parent_action_detected:
                logger.warning("부모 동작 미감지 → FAIL 예정, 시각화 영상 생성 중...")
            
            if not child_action_detected:
                logger.warning("아이 동작 미감지 → FAIL 예정, 시각화 영상 생성 중...")
            
            # 7. DTW ALIGNMENT
            logger.info("시간 정렬 중...")
            aligned_query, aligned_ref = self.dtw_aligner.align_sequences(
                query_normalized, ref_normalized
            )
            
            # 8. SIMILARITY CALCULATION
            logger.info("유사도 계산 중...")
            similarity_result = self.similarity_calculator.compute_similarity(
                aligned_query, aligned_ref, aligned=True, action_type=action_type
            )
            
            # 9. 지속 시간 계산 (정렬 후 유사도 기반)
            if child_action_detected:
                duration = self._calculate_duration(
                    similarity_result.frame_similarities,
                    video_info.fps,
                    threshold=threshold
                )
            else:
                duration = None  # 아이 동작 미감지 시 None
            
            # 10. 스켈레톤 동영상 생성 (메트릭 정보 포함)
            skeleton_video_path = None
            if save_skeleton_video:
                skeleton_video_path = output_path / "skeleton_video.mp4"
                
                # Trial 정보 구성 (RabbitMQ JSON과 동일한 구조)
                trial_info = {
                    "similarity_score": similarity_result.overall,
                    "attention_ratio": validity if 'validity' in locals() else self._calculate_validity(query_normalized),
                    "parent_start_time": reaction_delay_detail.get("parent_start_sec") if reaction_delay_detail else None,
                    "parent_end_time": (reaction_delay_detail.get("parent_start_sec", 0) + 3.0) if reaction_delay_detail else None,
                    "child_start_time": reaction_delay_detail.get("child_start_sec") if reaction_delay_detail else None,
                    "child_end_time": (reaction_delay_detail.get("child_start_sec", 0) + duration) if reaction_delay_detail and duration else None,
                    "latency_s": reaction_delay,
                    "duration_s": duration
                }
                
                self._create_skeleton_video_with_metrics(
                    viz_folder, 
                    skeleton_video_path, 
                    fps=self.video_processor.target_fps,
                    reaction_delay=reaction_delay,
                    duration=duration,
                    similarity_score=similarity_result.overall,
                    frame_similarities=similarity_result.frame_similarities,
                    reaction_delay_detail=reaction_delay_detail,
                    action_type=action_type,
                    threshold=threshold,
                    child_action_detected=child_action_detected,
                    trial_info=trial_info
                )
                logger.info(f"동영상 생성 완료: {skeleton_video_path}")
            
            validity = self._calculate_validity(query_normalized)
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # role_info에 반응 지연 상세 정보 추가
            if role_info and reaction_delay_detail:
                role_info["reaction_delay_detail"] = reaction_delay_detail
            
            # 최종 passed 판정
            if not child_action_detected:
                passed = False
                fail_reason = "child_action_not_detected"
            elif not parent_action_detected:
                passed = False
                fail_reason = "parent_action_not_detected"
            else:
                # 둘 다 감지됨 → 유사도 기준
                passed = similarity_result.overall >= threshold
                fail_reason = None if passed else "similarity_below_threshold"
            
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
                passed=passed,
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
                    "fail_reason": fail_reason,
                    "child_action_detected": child_action_detected,
                    "parent_action_detected": parent_action_detected,
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
    
    # 각 trial 구간 길이 (초)
    TRIAL_DURATION_SEC = 16.0

    def analyze_multi_trial(
        self,
        video_path: str,
        action_list: list[str],
        age_months: int,
        identify_roles: bool = True,
        smooth: bool = True,
        smooth_method: str = "one_euro"
    ) -> MultiTrialAnalysisResult:
        """
        다중 시도 동작 모방행동 분석 (pose_imitation).

        영상을 TRIAL_DURATION_SEC(16초)씩 구간 분할하여 각 trial을 분석합니다.
        - Trial 1: 0~16초
        - Trial 2: 16~32초
        - Trial 3: 32~48초

        Args:
            video_path: 분석할 영상 경로 (~48초 연속 영상)
            action_list: 동작 유형 리스트 (3개)
            age_months: 아동 월령
            identify_roles: 부모/아이 역할 자동 구분
            smooth: 스무딩 적용
            smooth_method: 스무딩 방법

        Returns:
            MultiTrialAnalysisResult: 다중 시도 분석 결과
        """
        start_time = datetime.now()
        logger.info(f"다중 시도 분석 시작: {len(action_list)} trials")

        if len(action_list) != 3:
            raise InvalidInputError(
                message="action_list must contain exactly 3 actions",
                field="action_list",
                value=action_list
            )

        trial_results = []
        role_info = None
        raw_trials = []

        for trial_idx, action_type in enumerate(action_list, start=1):
            seg_start = (trial_idx - 1) * self.TRIAL_DURATION_SEC
            seg_end = trial_idx * self.TRIAL_DURATION_SEC
            logger.info(
                f"Trial {trial_idx}/{len(action_list)}: "
                f"{action_type} ({seg_start:.0f}~{seg_end:.0f}s)"
            )

            try:
                single_result = self.analyze(
                    video_path=video_path,
                    action_type=action_type,
                    age_months=age_months,
                    use_parent_reference=True,
                    identify_roles=identify_roles,
                    smooth=smooth,
                    smooth_method=smooth_method,
                    start_sec=seg_start,
                    end_sec=seg_end,
                )

                if trial_idx == 1 and single_result.role_info:
                    role_info = single_result.role_info

                # 구간 내 상대 시간 → 전체 영상 절대 시간
                raw_latency = single_result.reaction_delay_sec
                latency = (
                    max(0.0, raw_latency)
                    if raw_latency is not None
                    else None
                )

                # reaction_delay_detail에서 부모/아이 시작 프레임 추출
                rd = single_result.details.get(
                    "reaction_delay_detail"
                ) or (
                    single_result.role_info.get(
                        "reaction_delay_detail"
                    ) if single_result.role_info else None
                )
                fps = single_result.details.get(
                    "video_fps",
                    self.video_processor.target_fps,
                )

                if rd and rd.get("parent_detected"):
                    parent_start_rel = (
                        rd["parent_start_frame"] / fps
                    )
                    parent_start = seg_start + parent_start_rel
                else:
                    parent_start = seg_start

                if rd and rd.get("child_detected"):
                    child_start_rel = (
                        rd["child_start_frame"] / fps
                    )
                    child_start = seg_start + child_start_rel
                else:
                    child_start = None

                parent_end = parent_start + 3.0

                raw_trials.append({
                    "trial_idx": trial_idx,
                    "action_type": action_type,
                    "success": single_result.passed,
                    "similarity_score": single_result.similarity_score,
                    "parent_start": parent_start,
                    "parent_end": parent_end,
                    "child_start": child_start,
                    "latency": latency,
                    "duration": single_result.duration_sec,
                    "attention_ratio": single_result.validity,
                })

                logger.info(
                    f"Trial {trial_idx} 완료: "
                    f"success={single_result.passed}, "
                    f"score={single_result.similarity_score:.4f}"
                )

            except Exception as e:
                logger.warning(f"Trial {trial_idx} 실패: {e}")
                raw_trials.append({
                    "trial_idx": trial_idx,
                    "action_type": action_type,
                    "success": False,
                    "similarity_score": 0.0,
                    "parent_start": seg_start,
                    "parent_end": seg_start + 3.0,
                    "child_start": None,
                    "latency": None,
                    "duration": None,
                    "attention_ratio": 0.0,
                })

        # child_end_time 계산 (구간 경계 내로 제한)
        for raw in raw_trials:
            child_start = raw["child_start"]
            duration = raw["duration"]

            if child_start is not None and duration is not None:
                child_end = child_start + duration
            else:
                child_end = None

            # 구간 경계를 초과하지 않도록 제한
            seg_boundary = raw["trial_idx"] * self.TRIAL_DURATION_SEC
            if child_end is not None and child_end > seg_boundary:
                child_end = seg_boundary
                duration = (
                    child_end - child_start
                    if child_start is not None
                    else None
                )

            trial = TrialResult(
                trial_index=raw["trial_idx"],
                action_type=raw["action_type"],
                success=raw["success"],
                similarity_score=raw["similarity_score"],
                parent_start_time=raw["parent_start"],
                parent_end_time=raw["parent_end"],
                child_start_time=child_start,
                child_end_time=child_end,
                latency_s=raw["latency"],
                duration_s=duration,
                attention_ratio=raw["attention_ratio"],
            )

            trial_results.append(trial.to_dict())

        processing_time = (datetime.now() - start_time).total_seconds()

        # ADOS 점수 계산
        ados_scores = self._calculate_ados_scores(trial_results)

        # 즐거움 감지 (표정 분석 모듈 사용)
        joy_result = self._detect_joy(video_path, trial_results)
        ados_scores["B6"] = joy_result["detected"]

        result = MultiTrialAnalysisResult(
            assessment_type="pose_imitation",
            age_months=age_months,
            processing_time_sec=processing_time,
            metrics={"per_trial": trial_results},
            ados=ados_scores,
            role_info=role_info,
            details={
                "action_list": action_list,
                "total_trials": len(action_list),
                "successful_trials": sum(
                    1 for t in trial_results if t["success"]
                ),
                "trial_duration_sec": self.TRIAL_DURATION_SEC,
                "smooth_method": smooth_method if smooth else None,
                "expression_analysis": {
                    "method": joy_result.get("method", "unknown"),
                    "joy_ratio": joy_result.get("ratio", 0.0),
                    "joy_count": joy_result.get("count", 0),
                    "frames_analyzed": joy_result.get(
                        "frames_analyzed", 0
                    ),
                },
            },
        )

        logger.info(
            f"다중 시도 분석 완료: "
            f"{result.details['successful_trials']}"
            f"/{len(action_list)} trials 성공"
        )
        return result

    def analyze_multi_trial_with_visualization(
        self,
        video_path: str,
        action_list: list[str],
        age_months: int,
        output_folder: str = "analysis_output",
        identify_roles: bool = True,
        smooth: bool = True,
        smooth_method: str = "one_euro",
    ) -> MultiTrialAnalysisResult:
        """
        다중 시도 분석 + 구간별 시각화 + 합본 영상 생성.

        영상을 16초씩 구간 분할하여 각 trial을 분석하고,
        구간별 스켈레톤 영상을 생성한 뒤 하나로 합본합니다.

        Args:
            video_path: 분석할 영상 경로 (~48초 연속 영상)
            action_list: 동작 유형 리스트 (3개)
            age_months: 아동 월령
            output_folder: 시각화 결과 저장 폴더
            identify_roles: 부모/아이 역할 자동 구분
            smooth: 스무딩 적용
            smooth_method: 스무딩 방법

        Returns:
            MultiTrialAnalysisResult: 분석 결과 (visualization_info 포함)
        """
        start_time = datetime.now()
        logger.info(
            f"다중 시도 시각화 분석 시작: {len(action_list)} trials"
        )

        if len(action_list) != 3:
            raise InvalidInputError(
                message="action_list must contain exactly 3 actions",
                field="action_list",
                value=action_list,
            )

        output_path = Path(output_folder)
        output_path.mkdir(parents=True, exist_ok=True)

        trial_analysis_results: list[AnalysisResult] = []
        trial_video_paths: list[Path | None] = []
        role_info = None
        raw_trials = []

        for trial_idx, action_type in enumerate(action_list, start=1):
            seg_start = (trial_idx - 1) * self.TRIAL_DURATION_SEC
            seg_end = trial_idx * self.TRIAL_DURATION_SEC
            trial_folder = str(
                output_path / f"trial_{trial_idx}_{action_type}"
            )

            logger.info(
                f"Trial {trial_idx}/{len(action_list)}: "
                f"{action_type} ({seg_start:.0f}~{seg_end:.0f}s)"
            )

            try:
                single_result = self.analyze_with_visualization(
                    video_path=video_path,
                    action_type=action_type,
                    age_months=age_months,
                    output_folder=trial_folder,
                    save_skeleton_video=True,
                    use_parent_reference=True,
                    identify_roles=identify_roles,
                    smooth=smooth,
                    smooth_method=smooth_method,
                    start_sec=seg_start,
                    end_sec=seg_end,
                )

                trial_analysis_results.append(single_result)

                # skeleton_video 경로 수집
                viz_info = single_result.visualization_info
                if viz_info and viz_info.get("skeleton_video"):
                    trial_video_paths.append(
                        Path(viz_info["skeleton_video"])
                    )
                else:
                    trial_video_paths.append(None)

                if trial_idx == 1 and single_result.role_info:
                    role_info = single_result.role_info

                # timing 계산
                raw_latency = single_result.reaction_delay_sec
                latency = (
                    max(0.0, raw_latency)
                    if raw_latency is not None
                    else None
                )

                rd = single_result.details.get(
                    "reaction_delay_detail"
                ) or (
                    single_result.role_info.get(
                        "reaction_delay_detail"
                    ) if single_result.role_info else None
                )
                fps = single_result.details.get(
                    "video_fps",
                    self.video_processor.target_fps,
                )

                if rd and rd.get("parent_detected"):
                    parent_start = (
                        seg_start
                        + rd["parent_start_frame"] / fps
                    )
                else:
                    parent_start = seg_start

                if rd and rd.get("child_detected"):
                    child_start = (
                        seg_start
                        + rd["child_start_frame"] / fps
                    )
                else:
                    child_start = None

                parent_end = parent_start + 3.0

                raw_trials.append({
                    "trial_idx": trial_idx,
                    "action_type": action_type,
                    "success": single_result.passed,
                    "similarity_score": single_result.similarity_score,
                    "parent_start": parent_start,
                    "parent_end": parent_end,
                    "child_start": child_start,
                    "latency": latency,
                    "duration": single_result.duration_sec,
                    "attention_ratio": single_result.validity,
                })

                logger.info(
                    f"Trial {trial_idx} 시각화 완료: "
                    f"success={single_result.passed}, "
                    f"score={single_result.similarity_score:.4f}"
                )

            except Exception as e:
                logger.warning(
                    f"Trial {trial_idx} 실패: {e}", exc_info=True
                )
                trial_video_paths.append(None)
                raw_trials.append({
                    "trial_idx": trial_idx,
                    "action_type": action_type,
                    "success": False,
                    "similarity_score": 0.0,
                    "parent_start": seg_start,
                    "parent_end": seg_start + 3.0,
                    "child_start": None,
                    "latency": None,
                    "duration": None,
                    "attention_ratio": 0.0,
                })

        # child_end 계산 (구간 경계 내로 제한)
        trial_results = []
        for raw in raw_trials:
            child_start = raw["child_start"]
            duration = raw["duration"]

            if child_start is not None and duration is not None:
                child_end = child_start + duration
            else:
                child_end = None

            seg_boundary = raw["trial_idx"] * self.TRIAL_DURATION_SEC
            if child_end is not None and child_end > seg_boundary:
                child_end = seg_boundary
                duration = (
                    child_end - child_start
                    if child_start is not None
                    else None
                )

            trial = TrialResult(
                trial_index=raw["trial_idx"],
                action_type=raw["action_type"],
                success=raw["success"],
                similarity_score=raw["similarity_score"],
                parent_start_time=raw["parent_start"],
                parent_end_time=raw["parent_end"],
                child_start_time=child_start,
                child_end_time=child_end,
                latency_s=raw["latency"],
                duration_s=duration,
                attention_ratio=raw["attention_ratio"],
            )
            trial_results.append(trial.to_dict())

        # ADOS 점수 계산
        ados_scores = self._calculate_ados_scores(trial_results)
        joy_result = self._detect_joy(video_path, trial_results)
        ados_scores["B6"] = joy_result["detected"]

        # 합본 영상 생성
        merged_video_path = output_path / "시각화최종.mp4"
        self._merge_trial_videos(
            trial_video_paths=trial_video_paths,
            trial_results=trial_results,
            output_path=merged_video_path,
            fps=self.video_processor.target_fps,
        )

        processing_time = (datetime.now() - start_time).total_seconds()

        result = MultiTrialAnalysisResult(
            assessment_type="pose_imitation",
            age_months=age_months,
            processing_time_sec=processing_time,
            metrics={"per_trial": trial_results},
            ados=ados_scores,
            role_info=role_info,
            details={
                "action_list": action_list,
                "total_trials": len(action_list),
                "successful_trials": sum(
                    1 for t in trial_results if t["success"]
                ),
                "trial_duration_sec": self.TRIAL_DURATION_SEC,
                "smooth_method": smooth_method if smooth else None,
                "expression_analysis": {
                    "method": joy_result.get("method", "unknown"),
                    "joy_ratio": joy_result.get("ratio", 0.0),
                    "joy_count": joy_result.get("count", 0),
                    "frames_analyzed": joy_result.get(
                        "frames_analyzed", 0
                    ),
                },
                "visualization": {
                    "output_folder": str(output_path),
                    "merged_video": str(merged_video_path),
                    "trial_videos": [
                        str(p) if p else None
                        for p in trial_video_paths
                    ],
                },
            },
        )

        logger.info(
            f"다중 시도 시각화 분석 완료: "
            f"{result.details['successful_trials']}"
            f"/{len(action_list)} trials 성공 "
            f"→ {merged_video_path}"
        )
        return result

    def _calculate_ados_scores(self, trial_results: list[dict]) -> dict[str, Any]:
        """
        ADOS 점수 계산.
        
        Args:
            trial_results: Trial 결과 리스트
            
        Returns:
            ADOS 점수 딕셔너리 {"B6": bool, "A8": int, "B18": bool}
            
        Note:
            - B18: 1개 이상 성공 시 True
            - A8: success 개수 기반 (3개=0점, 2개=1점, 1개=2점, 0개=3점)
            - B6: 얼굴 표정 분석으로 즐거움 감지 여부 (별도 모듈에서 처리)
        """
        successful_count = sum(1 for t in trial_results if t["success"])
        
        # B18: 사회적 모방 - 1개 이상 성공 시 True
        b18 = successful_count >= 1
        
        # A8: 주의 및 반응 - success 개수에 따라 점수 부여 (0-3점)
        if successful_count == 3:
            a8 = 0  # 모두 성공: 0점 (가장 좋음)
        elif successful_count == 2:
            a8 = 1  # 2개 성공: 1점
        elif successful_count == 1:
            a8 = 2  # 1개 성공: 2점
        else:  # successful_count == 0
            a8 = 3  # 모두 실패: 3점 (가장 나쁨)
        
        # B6: 즐거움 감지 - 얼굴 표정 분석 모듈에서 처리 (여기서는 placeholder)
        # 실제로는 _detect_joy() 결과를 사용하여 설정됨
        b6 = False  # placeholder, 나중에 joy 결과로 업데이트
        
        return {
            "B6": b6,  # 즐거움 감지 (얼굴 표정 분석)
            "A8": a8,  # 주의 및 반응 (0-3점)
            "B18": b18  # 사회적 모방 (1개 이상 성공)
        }
    
    def _detect_joy(
        self,
        video_path: str,
        trial_results: list[dict]
    ) -> dict[str, Any]:
        """
        얼굴 표정에서 즐거움 감지.
        
        Args:
            video_path: 분석할 영상 경로
            trial_results: Trial 결과 리스트
            
        Returns:
            즐거움 감지 결과 {"detected": bool, "count": int, "ratio": float, ...}
        """
        # 표정 분석기가 사용 가능한 경우 실제 분석 수행
        if self.expression_analyzer and self.expression_analyzer.available:
            try:
                # 전체 영상 분석 (0~48초)
                return self._detect_joy_with_expression_analyzer(
                    video_path, 
                    start_sec=0.0, 
                    end_sec=48.0
                )
            except Exception as e:
                logger.warning(f"표정 분석 실패, fallback 사용: {e}")
        
        # Fallback: 표정 분석이 안 되었으므로 False 처리
        logger.warning("즐거움 감지 실패: ExpressionAnalyzer 사용 불가 (detected=False)")
        
        return {
            "detected": False,
            "count": 0,
            "ratio": 0.0,
            "confidence": 0.0,
            "method": "unavailable",
            "note": "ExpressionAnalyzer not available, cannot detect joy"
        }
    
    def _detect_joy_with_expression_analyzer(
        self,
        video_path: str,
        start_sec: float = 0.0,
        end_sec: Optional[float] = None
    ) -> dict[str, Any]:
        """
        ExpressionAnalyzer를 사용한 실제 표정 분석.
        
        Args:
            video_path: 분석할 영상 경로
            start_sec: 시작 시간 (초)
            end_sec: 종료 시간 (초)
            
        Returns:
            표정 분석 결과
        """
        import cv2
        
        logger.info("표정 분석 시작 (ExpressionAnalyzer)")
        
        # 1. 포즈 추출 및 역할 식별로 아이 머리 위치 파악
        try:
            extraction_result = self.video_processor.extract_frames(
                video_path, start_sec=start_sec, end_sec=end_sec
            )
            frames_data = self.pose_extractor.extract_from_folder(extraction_result.frames_folder)
            
            # 역할 식별
            frame_persons = self.role_identifier.identify_roles(frames_data)
            
            # 아이 머리 위치 추출 (코 키포인트 기준)
            child_head_positions = []
            frames = []
            
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                raise PipelineError(
                    message=f"영상을 열 수 없습니다: {video_path}",
                    code="VIDEO_OPEN_ERROR",
                    details={"video_path": video_path}
                )
            
            # 시작/종료 시간 설정
            fps = cap.get(cv2.CAP_PROP_FPS)
            if start_sec > 0:
                cap.set(cv2.CAP_PROP_POS_FRAMES, int(start_sec * fps))
            
            frame_idx = 0
            max_frames = int((end_sec - start_sec) * fps) if end_sec else None
            
            try:
                while True:
                    if max_frames and frame_idx >= max_frames:
                        break
                    
                    ret, frame = cap.read()
                    if not ret:
                        break
                    
                    frames.append(frame)
                    
                    # 아이 머리 위치 찾기
                    child_pos = None
                    if frame_idx < len(frame_persons):
                        fp = frame_persons[frame_idx]
                        if fp.child and fp.child.person_pose and fp.child.person_pose.keypoints:
                            # 코(nose) 키포인트 사용
                            nose = fp.child.person_pose.keypoints.get("nose")
                            if nose and nose["score"] > 0.3:
                                child_pos = (int(nose["x"]), int(nose["y"]))
                    
                    child_head_positions.append(child_pos)
                    frame_idx += 1
                    
            finally:
                cap.release()
            
            if not frames:
                logger.warning("프레임을 추출할 수 없습니다")
                return {
                    "detected": False,
                    "count": 0,
                    "ratio": 0.0,
                    "method": "expression_analyzer",
                    "error": "no_frames"
                }
            
            logger.info(f"아이 머리 위치 {sum(1 for p in child_head_positions if p is not None)}/{len(child_head_positions)} 프레임 탐지됨")
            
            # 표정 분석 수행 (아이 머리 위치 전달)
            expression_result = self.expression_analyzer.analyze(
                frames=frames,
                child_head_positions=child_head_positions,
                parent_head_positions=None
            )
            
        except Exception as e:
            logger.error(f"포즈 기반 표정 분석 실패: {e}")
            return {
                "detected": False,
                "count": 0,
                "ratio": 0.0,
                "method": "expression_analyzer",
                "error": f"pose_based_analysis_failed: {str(e)}"
            }
        
        logger.info(
            f"표정 분석 완료: joy_detected={expression_result.joy_detected}, "
            f"joy_count={expression_result.joy_count}, "
            f"joy_ratio={expression_result.joy_ratio:.1%}"
        )
        
        return {
            "detected": expression_result.joy_detected,
            "count": expression_result.joy_count,
            "ratio": round(expression_result.joy_ratio, 4),
            "dominant": expression_result.dominant_emotion,
            "distribution": {k: round(v, 4) for k, v in expression_result.expression_ratios.items()},
            "method": "expression_analyzer",
            "frames_analyzed": expression_result.total_frames_analyzed,
            "valid_detections": expression_result.valid_detections,
            "processing_time_sec": round(expression_result.processing_time_sec, 2)
        }
    
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
    
    def _create_skeleton_video_with_metrics(
        self,
        frames_folder: Path,
        output_path: Path,
        fps: float,
        reaction_delay: float,
        duration: float,
        similarity_score: float,
        frame_similarities: list[float],
        reaction_delay_detail: dict,
        action_type: str,
        threshold: float,
        child_action_detected: bool = True,
        trial_info: Optional[dict] = None
    ) -> None:
        """
        시각화된 프레임들을 메트릭 정보와 함께 동영상으로 합성.
        
        부모/아이 동작 시작 시점을 강조 표시합니다.
        
        Args:
            frames_folder: 시각화된 프레임 폴더
            output_path: 출력 동영상 경로
            fps: 동영상 FPS
            reaction_delay: 반응 지연 시간 (초)
            duration: 동작 지속 시간 (초)
            similarity_score: 전체 유사도 점수 (코사인 유사도)
            frame_similarities: 프레임별 유사도
            reaction_delay_detail: 반응 지연 상세 정보
            action_type: 동작 타입
            threshold: 통과 임계값
            child_action_detected: 아이 동작 감지 여부 (기본값 True)
            trial_info: Trial 결과 정보 (attention_ratio, parent/child 시간 등)
        """
        import cv2
        
        frame_files = sorted(frames_folder.glob(f"viz_*{IMAGE_EXTENSION}"))
        
        if not frame_files:
            logger.warning("시각화된 프레임이 없습니다.")
            return
        
        # 첫 프레임으로 크기 확인
        first_frame = cv2.imread(str(frame_files[0]))
        height, width = first_frame.shape[:2]
        
        # 좌측 오버레이 패널 너비
        overlay_width = 320
        
        # 비디오 라이터 (원본 크기 유지)
        fourcc = cv2.VideoWriter_fourcc(*VIDEO_FOURCC)
        out = cv2.VideoWriter(str(output_path), fourcc, fps, (width, height))
        
        # 반응 지연 상세 정보 추출 (None 처리)
        parent_start_frame = reaction_delay_detail.get("parent_start_frame") if reaction_delay_detail else None
        child_start_frame = reaction_delay_detail.get("child_start_frame") if reaction_delay_detail else None
        detection_method = reaction_delay_detail.get("detection_method", "unknown") if reaction_delay_detail else "unknown"
        parent_detected = reaction_delay_detail.get("parent_detected", False) if reaction_delay_detail else False
        child_detected = reaction_delay_detail.get("child_detected", False) if reaction_delay_detail else False
        
        # 강조 지속 프레임 수 (0.5초)
        highlight_duration = int(fps * 0.5)
        
        # Trial 정보 추출 (RabbitMQ JSON 데이터 활용)
        attention_ratio = trial_info.get("attention_ratio") if trial_info else None
        parent_start_time = trial_info.get("parent_start_time") if trial_info else None
        parent_end_time = trial_info.get("parent_end_time") if trial_info else None
        child_start_time = trial_info.get("child_start_time") if trial_info else None
        child_end_time = trial_info.get("child_end_time") if trial_info else None
        latency_s = trial_info.get("latency_s") if trial_info else None
        
        for frame_idx, frame_path in enumerate(frame_files):
            frame = cv2.imread(str(frame_path))
            frame_time = frame_idx / fps
            
            # ========== 좌측 정보 오버레이 (반투명 배경) ==========
            # 배경 오버레이 그리기
            overlay = frame.copy()
            cv2.rectangle(overlay, (0, 0), (overlay_width, height), (40, 40, 40), -1)
            # 반투명 블렌딩 (알파=0.85 → 85% 불투명)
            cv2.addWeighted(overlay, 0.85, frame, 0.15, 0, frame)
            
            y_pos = 30  # 세로 위치 시작
            
            # 동작 타입 및 결과
            passed = similarity_score >= threshold and child_action_detected
            result_text = f"{action_type.upper()}"
            result_color = (0, 255, 0) if passed else (0, 0, 255)
            cv2.putText(frame, result_text, (10, y_pos), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
            y_pos += 30
            
            status_text = "PASS" if passed else "FAIL"
            cv2.putText(frame, status_text, (10, y_pos), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1.0, result_color, 2)
            y_pos += 50
            
            # 구분선
            cv2.line(frame, (10, y_pos), (overlay_width - 10, y_pos), (100, 100, 100), 1)
            y_pos += 20
            
            # 전체 유사도 (코사인 기반)
            cv2.putText(frame, "Cosine Similarity:", (10, y_pos),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
            y_pos += 25
            cv2.putText(frame, f"{similarity_score:.1%}", (10, y_pos),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 0), 2)
            y_pos += 30
            
            # Threshold
            cv2.putText(frame, f"Threshold: {threshold:.1%}", (10, y_pos),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (150, 150, 150), 1)
            y_pos += 30
            
            # 구분선
            cv2.line(frame, (10, y_pos), (overlay_width - 10, y_pos), (100, 100, 100), 1)
            y_pos += 20
            
            # 반응 지연 시간
            if latency_s is not None:
                delay_text = f"Latency: {latency_s:.2f}s"
            elif reaction_delay is not None:
                delay_text = f"Latency: {reaction_delay:.2f}s"
            else:
                delay_text = "Latency: N/A"
            cv2.putText(frame, delay_text, (10, y_pos),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
            y_pos += 30
            
            # 동작 지속 시간
            if duration is not None:
                duration_text = f"Duration: {duration:.2f}s"
            else:
                duration_text = "Duration: N/A"
            cv2.putText(frame, duration_text, (10, y_pos),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 200, 100), 1)
            y_pos += 30
            
            # 주의력/상호작용 비율
            if attention_ratio is not None:
                attention_text = f"Attention: {attention_ratio:.1%}"
                attention_color = (0, 255, 0) if attention_ratio >= 0.7 else (100, 200, 255)
                cv2.putText(frame, attention_text, (10, y_pos),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, attention_color, 1)
                y_pos += 35
            
            # 구분선
            cv2.line(frame, (10, y_pos), (overlay_width - 10, y_pos), (100, 100, 100), 1)
            y_pos += 20
            
            # 부모 동작 시간
            if parent_start_time is not None and parent_end_time is not None:
                cv2.putText(frame, "Parent Action:", (10, y_pos),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.45, (200, 200, 200), 1)
                y_pos += 20
                cv2.putText(frame, f"{parent_start_time:.1f}s - {parent_end_time:.1f}s", (10, y_pos),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 150, 100), 1)
                y_pos += 25
            
            # 아이 동작 시간
            if child_start_time is not None and child_end_time is not None:
                cv2.putText(frame, "Child Action:", (10, y_pos),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.45, (200, 200, 200), 1)
                y_pos += 20
                cv2.putText(frame, f"{child_start_time:.1f}s - {child_end_time:.1f}s", (10, y_pos),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.45, (100, 200, 255), 1)
                y_pos += 30
            
            # 구분선
            cv2.line(frame, (10, y_pos), (overlay_width - 10, y_pos), (100, 100, 100), 1)
            y_pos += 20
            
            # 현재 시간 / 프레임
            cv2.putText(frame, f"Time: {frame_time:.2f}s", (10, y_pos),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
            y_pos += 20
            cv2.putText(frame, f"Frame: {frame_idx}", (10, y_pos),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
            y_pos += 25
            
            # 감지 방식
            cv2.putText(frame, f"Method: {detection_method}", (10, y_pos),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.4, (150, 150, 150), 1)
            
            # ========== 부모 동작 시작 강조 ==========
            if parent_detected and parent_start_frame is not None:
                if parent_start_frame <= frame_idx < parent_start_frame + highlight_duration:
                    # 파란색 테두리
                    border_thickness = 8
                    cv2.rectangle(frame, (0, 0), (width - 1, height - 1), 
                                 (255, 100, 0), border_thickness)
                    
                    # 부모 시작 텍스트 (화면 중앙)
                    text = "PARENT ACTION START!"
                    text_size = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 1.2, 3)[0]
                    text_x = (width - text_size[0]) // 2
                    text_y = height // 2 - 50
                    
                    # 텍스트 배경
                    cv2.rectangle(frame, (text_x - 10, text_y - 35), 
                                 (text_x + text_size[0] + 10, text_y + 10), (255, 100, 0), -1)
                    cv2.putText(frame, text, (text_x, text_y), 
                               cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 255), 3)
                    
                    # 시간 표시
                    parent_time = parent_start_frame / fps
                    time_text = f"Frame {parent_start_frame} ({parent_time:.2f}s)"
                    time_size = cv2.getTextSize(time_text, cv2.FONT_HERSHEY_SIMPLEX, 0.8, 2)[0]
                    cv2.putText(frame, time_text, (text_x + (text_size[0] - time_size[0]) // 2, text_y + 40),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 200, 100), 2)
            
            # ========== 아이 동작 시작 강조 ==========
            if child_detected and child_start_frame is not None:
                if child_start_frame <= frame_idx < child_start_frame + highlight_duration:
                    # 주황색 테두리
                    border_thickness = 8
                    cv2.rectangle(frame, (0, 0), (width - 1, height - 1), 
                                 (0, 165, 255), border_thickness)
                    
                    # 아이 시작 텍스트 (화면 중앙)
                    text = "CHILD ACTION START!"
                    text_size = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 1.2, 3)[0]
                    text_x = (width - text_size[0]) // 2
                    text_y = height // 2 + 50
                    
                    # 텍스트 배경
                    cv2.rectangle(frame, (text_x - 10, text_y - 35), 
                                 (text_x + text_size[0] + 10, text_y + 10), (0, 165, 255), -1)
                    cv2.putText(frame, text, (text_x, text_y), 
                               cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 255), 3)
                    
                    # 시간 및 지연 표시
                    child_time = child_start_frame / fps
                    delay_text = f"Frame {child_start_frame} ({child_time:.2f}s) | Delay: {reaction_delay:.2f}s"
                    delay_size = cv2.getTextSize(delay_text, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)[0]
                    cv2.putText(frame, delay_text, ((width - delay_size[0]) // 2, text_y + 40),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (100, 255, 200), 2)
            
            # ========== 아이 동작 미감지 경고 (화면 하단) ==========
            if not child_action_detected:
                warning_text = "CHILD ACTION NOT DETECTED!"
                warning_size = cv2.getTextSize(warning_text, cv2.FONT_HERSHEY_SIMPLEX, 1.2, 3)[0]
                warning_x = (width - warning_size[0]) // 2
                warning_y = height - 50
                
                # 배경
                cv2.rectangle(frame, (warning_x - 10, warning_y - 35), 
                             (warning_x + warning_size[0] + 10, warning_y + 10), 
                             (0, 0, 255), -1)
                # 텍스트
                cv2.putText(frame, warning_text, (warning_x, warning_y), 
                           cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 255), 3)
            
            out.write(frame)
        
        out.release()
        logger.debug(f"메트릭 포함 동영상 생성: {output_path} ({len(frame_files)} frames, {fps}fps)")

    def _merge_trial_videos(
        self,
        trial_video_paths: list[Path],
        trial_results: list[dict],
        output_path: Path,
        fps: float,
    ) -> None:
        """
        개별 trial 스켈레톤 영상들을 하나로 합본.

        각 trial 영상 사이에 구분 타이틀 프레임(1초)을 삽입합니다.

        Args:
            trial_video_paths: trial별 skeleton_video.mp4 경로 리스트
            trial_results: trial별 분석 결과 dict 리스트
            output_path: 합본 영상 출력 경로
            fps: 출력 영상 FPS
        """
        import cv2

        # 첫 영상에서 해상도 확인
        first_valid = None
        for p in trial_video_paths:
            if p and p.exists():
                first_valid = p
                break
        if first_valid is None:
            logger.warning("합본할 trial 영상이 없습니다.")
            return

        cap = cv2.VideoCapture(str(first_valid))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        cap.release()

        fourcc = cv2.VideoWriter_fourcc(*VIDEO_FOURCC)
        out = cv2.VideoWriter(
            str(output_path), fourcc, fps, (width, height)
        )

        title_frames = int(fps * 1.0)  # 구분 타이틀 1초

        for idx, (video_path, trial) in enumerate(
            zip(trial_video_paths, trial_results, strict=True)
        ):
            action = trial.get("action_type", "unknown")
            trial_num = trial.get("trial_index", idx + 1)
            passed = trial.get("success", False)
            score = trial.get("similarity_score", 0.0)

            # ── 구분 타이틀 프레임 삽입 ──
            for _ in range(title_frames):
                title = np.zeros((height, width, 3), dtype=np.uint8)

                # Trial 번호 + 동작명
                header = f"Trial {trial_num}: {action.upper()}"
                h_size = cv2.getTextSize(
                    header, cv2.FONT_HERSHEY_SIMPLEX, 1.5, 3
                )[0]
                h_x = (width - h_size[0]) // 2
                cv2.putText(
                    title, header, (h_x, height // 2 - 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.5,
                    (255, 255, 255), 3,
                )

                # PASS/FAIL + 유사도
                result_text = (
                    f"{'PASS' if passed else 'FAIL'}"
                    f" ({score:.1%})"
                )
                r_color = (0, 255, 0) if passed else (0, 0, 255)
                r_size = cv2.getTextSize(
                    result_text, cv2.FONT_HERSHEY_SIMPLEX, 1.2, 2
                )[0]
                r_x = (width - r_size[0]) // 2
                cv2.putText(
                    title, result_text, (r_x, height // 2 + 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.2, r_color, 2,
                )

                out.write(title)

            # ── trial 영상 프레임 복사 ──
            if video_path and video_path.exists():
                cap = cv2.VideoCapture(str(video_path))
                while True:
                    ret, frame = cap.read()
                    if not ret:
                        break
                    # 해상도 불일치 시 리사이즈
                    if (
                        frame.shape[1] != width
                        or frame.shape[0] != height
                    ):
                        frame = cv2.resize(
                            frame, (width, height)
                        )
                    out.write(frame)
                cap.release()
            else:
                # 영상 없으면 빈 프레임으로 채움 (1초)
                for _ in range(int(fps)):
                    blank = np.zeros(
                        (height, width, 3), dtype=np.uint8
                    )
                    cv2.putText(
                        blank,
                        f"Trial {trial_num}: No Video",
                        (width // 4, height // 2),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.0,
                        (100, 100, 100), 2,
                    )
                    out.write(blank)

        out.release()
        logger.info(f"합본 영상 생성 완료: {output_path}")


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
        
        # 아이 동작 미감지 시 특별 처리
        if result.details.get("fail_reason") == "child_action_not_detected":
            print(f"  통과 여부: ❌ FAIL (아이 동작 미감지)")
            print(f"  유사도 점수: 측정 불가")
            print(f"  적용 기준: {result.threshold_used:.2%}")
            print(f"  반응 지연: 측정 불가 (아이 동작 없음)")
            print(f"  동작 지속: 측정 불가 (아이 동작 없음)")
        else:
            print(f"  통과 여부: {'⭕ PASS' if result.passed else '😭 FAIL'}")
            print(f"  유사도 점수: {result.similarity_score:.2%}")
            print(f"  적용 기준: {result.threshold_used:.2%}")
            if result.reaction_delay_sec is not None:
                print(f"  반응 지연: {result.reaction_delay_sec:.2f}초")
            else:
                print(f"  반응 지연: 측정 불가")
            if result.duration_sec is not None:
                print(f"  동작 지속: {result.duration_sec:.2f}초")
            else:
                print(f"  동작 지속: 측정 불가")
        print(f"  분석 유효성: {result.validity:.2%}")
        print(f"  처리 시간: {result.processing_time_sec:.2f}초")
        
        # 상세 정보 (아이 동작 감지된 경우만)
        if result.details.get("fail_reason") != "child_action_not_detected":
            print("\n👶 상세 정보:")
            if result.details.get('upper_body_score') is not None:
                print(f"  상체 점수: {result.details['upper_body_score']:.2%}")
            if result.details.get('lower_body_score') is not None:
                print(f"  하체 점수: {result.details['lower_body_score']:.2%}")
            if result.details.get('head_score') is not None:
                print(f"  머리 점수: {result.details['head_score']:.2%}")
            print(f"  분석 프레임: {result.details.get('total_frames_analyzed', 'N/A')}개")
            if result.details.get('valid_frame_ratio') is not None:
                print(f"  유효 프레임 비율: {result.details['valid_frame_ratio']:.2%}")
        
        if result.role_info:
            print("\n👶 역할 식별 정보:")
            print(f"  부모 감지: {'⭕' if result.role_info['parent_identified'] else '😭'}")
            print(f"  아이 감지: {'⭕' if result.role_info['child_identified'] else '😭'}")
            if result.role_info.get('parent_torso_length'):
                print(f"  부모 몸통 길이: {result.role_info['parent_torso_length']:.1f}px")
            if result.role_info.get('child_torso_length'):
                print(f"  아이 몸통 길이: {result.role_info['child_torso_length']:.1f}px")
            
            # 반응 지연 상세 정보 출력
            if result.role_info.get('reaction_delay_detail'):
                detail = result.role_info['reaction_delay_detail']
                print("\n👶 반응 지연 상세:")
                
                # 부모 동작 감지 여부
                if detail.get('parent_detected', False):
                    print(f"  부모 동작 시작: 프레임 {detail['parent_start_frame']} ({detail['parent_start_sec']:.2f}초)")
                else:
                    print(f"  부모 동작 시작: 미감지")
                
                # 아이 동작 감지 여부
                if detail.get('child_detected', False):
                    print(f"  아이 동작 시작: 프레임 {detail['child_start_frame']} ({detail['child_start_sec']:.2f}초)")
                else:
                    print(f"  아이 동작 시작: 미감지 ❌")
                
                # 지연 프레임 (둘 다 감지된 경우만)
                if detail.get('delay_frames') is not None:
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
        print("⭕ 분석 완료!")
        print("=" * 60 + "\n")
        
    except Exception as e:
        print(f"\n✖️ 분석 실패: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()