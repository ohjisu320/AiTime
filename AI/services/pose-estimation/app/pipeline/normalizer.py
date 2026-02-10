# AI/services/pose-estimation/app/pipeline/normalizer.py
"""
관절 좌표 정규화 모듈.

다양한 체형, 카메라 거리에 관계없이 일관된 비교가 가능하도록
관절 좌표를 정규화합니다.

역할 :
PoseExtractor가 뽑아낸 프레임별 다중 인물 포즈를 
→ (부모/아이 식별) → (정규화) → (시간 스무딩)까지 한 번에 처리해, 
최종 분석 입력 시퀀스를 만듭니다.

주요 기능:
1. 부모/아이 역할 구분
2. 정규화 (몸통 기준, 바운딩 박스 기준 등)
3. 시계열 스무딩 (이동 평균, 지수 이동 평균, One Euro Filter 등)    
"""

import numpy as np
import logging
from enum import Enum
from typing import Literal, Optional, TYPE_CHECKING
from dataclasses import dataclass, field

from app.config import settings
from app.pipeline.exceptions import NormalizationError
from app.pipeline.pose_extractor import KeypointIndex

if TYPE_CHECKING:
    from app.pipeline.pose_extractor import PersonPose, FramePoseData

logger = logging.getLogger(__name__)

NormalizationMethod = Literal["torso", "bbox", "hip_center"]
SmoothingMethod = Literal["none", "moving_avg", "exponential", "one_euro", "gaussian"]

# =============================================================================
# 상용 상수 (하드코딩 제거)
# =============================================================================
NUM_KEYPOINTS = 17
EPSILON = 1e-6

# Smoothing 관련
DEFAULT_SMOOTH_WINDOW = 5
DEFAULT_EMA_ALPHA = 0.3
DEFAULT_ONE_EURO_MIN_CUTOFF = 1.0
DEFAULT_ONE_EURO_BETA = 0.007
DEFAULT_ONE_EURO_D_CUTOFF = 1.0
DEFAULT_ONE_EURO_RATE = 30.0
GAUSSIAN_SIGMA_FACTOR = 4.0

# 정규화 관련
DEFAULT_FALLBACK_SCALE = 100.0

# 역할 구분(Identification) 관련
DEFAULT_IOU_THRESHOLD = 0.3
DEFAULT_SWAP_WINDOW = 5
CHILD_TORSO_RATIO_FALLBACK = 0.8

# 신뢰도(Confidence) 관련
CONF_SINGLE_ROLE = 0.7
CONF_GLOBAL_MATCH = 0.85
CONF_PREV_MATCH = 0.95
CONF_NEW_MATCH = 0.8
CONF_LOW = 0.5
CONF_IOU_MATCH_BASE = 0.9
CONF_IOU_MATCH_WEIGHT = 0.1
CONF_UNMATCHED_GLOBAL = 0.7
CONF_SWAP_FIX = 0.85

# 가중치 및 임계값
COMBINED_TORSO_WEIGHT = 0.7
COMBINED_BBOX_WEIGHT = 0.3
ROLE_DIFFERENCE_RATIO_THRESHOLD = 1.2
SWAP_DISTANCE_THRESHOLD_RATIO = 0.7


# =============================================================================
# 데이터 구조
# =============================================================================

class PersonRole(Enum):
    """사람 역할 구분"""
    UNKNOWN = "unknown"
    PARENT = "parent"   # 부모 (참조 동작, 보통 더 큼)
    CHILD = "child"     # 아이 (분석 대상, 보통 더 작음)


@dataclass
class IdentifiedPerson:
    """역할이 식별된 사람"""
    person_pose: "PersonPose"    # 원본 자세 데이터
    role: PersonRole             # 역할 (부모/아이)
    torso_length: float          # 몸통 길이 (어깨-골반)
    skeleton_height: float       # 전체 스켈레톤 높이
    bbox_area: float             # 바운딩 박스 면적
    role_confidence: float       # 역할 판정 신뢰도
    
    def to_array(self) -> np.ndarray:
        """키포인트를 numpy 배열로 변환 (NUM_KEYPOINTS, 3)"""
        keypoints = self.person_pose.keypoints
        result = np.zeros((NUM_KEYPOINTS, 3))
        
        # ViTPose 모델의 keypoint 키 형식: "Nose", "L_Eye", "L_Shoulder" 등
        keypoint_mapping = [
            ["Nose", "nose"],
            ["L_Eye", "left_eye"],
            ["R_Eye", "right_eye"],
            ["L_Ear", "left_ear"],
            ["R_Ear", "right_ear"],
            ["L_Shoulder", "left_shoulder"],
            ["R_Shoulder", "right_shoulder"],
            ["L_Elbow", "left_elbow"],
            ["R_Elbow", "right_elbow"],
            ["L_Wrist", "left_wrist"],
            ["R_Wrist", "right_wrist"],
            ["L_Hip", "left_hip"],
            ["R_Hip", "right_hip"],
            ["L_Knee", "left_knee"],
            ["R_Knee", "right_knee"],
            ["L_Ankle", "left_ankle"],
            ["R_Ankle", "right_ankle"]
        ]
        
        for i, aliases in enumerate(keypoint_mapping):
            for alias in aliases:
                if alias in keypoints:
                    kp = keypoints[alias]
                    result[i] = [kp["x"], kp["y"], kp["score"]]
                    break
        
        return result


@dataclass
class FramePersons:
    """프레임별 식별된 사람들"""
    frame_idx: int
    parent: Optional[IdentifiedPerson] = None
    child: Optional[IdentifiedPerson] = None
    num_detected: int = 0


@dataclass
class MultiPersonResult:
    """다중 인물 정규화 결과"""
    parent_sequence: Optional[np.ndarray]    # 부모 시퀀스 (T, NUM_KEYPOINTS, 3) or None
    child_sequence: np.ndarray               # 아이 시퀀스 (T, NUM_KEYPOINTS, 3)
    parent_raw: Optional[np.ndarray]         # 정규화 전 부모 시퀀스
    child_raw: np.ndarray                    # 정규화 전 아이 시퀀스
    frame_persons: list[FramePersons]        # 프레임별 역할 정보
    parent_avg_torso: Optional[float]        # 부모 평균 torso 길이
    child_avg_torso: float                   # 아이 평균 torso 길이


# =============================================================================
# Smoother 클래스
# =============================================================================

class Smoother:
    """
    시계열 스무딩 유틸리티.
    
    관절 좌표의 시간적 노이즈를 제거합니다.
    
    Attributes:
        method: 스무딩 방법
        window_size: 이동 평균 윈도우 크기
        alpha: EMA 계수
        min_cutoff: One Euro Filter 최소 cutoff
        beta: One Euro Filter 속도 계수
    """
    
    def __init__(
        self,
        method: SmoothingMethod = "exponential",
        window_size: int = DEFAULT_SMOOTH_WINDOW,
        alpha: float = DEFAULT_EMA_ALPHA,
        min_cutoff: float = DEFAULT_ONE_EURO_MIN_CUTOFF,
        beta: float = DEFAULT_ONE_EURO_BETA,
        d_cutoff: float = DEFAULT_ONE_EURO_D_CUTOFF
    ):
        """
        Smoother 초기화.
        
        Args:
            method: 스무딩 방법
            window_size: 이동 평균 윈도우 크기
            alpha: EMA 지수 가중치 (0~1, 낮을수록 스무딩 강함)
            min_cutoff: One Euro 최소 cutoff 주파수
            beta: One Euro 속도 계수 (높을수록 빠른 움직임에 민감)
            d_cutoff: One Euro 미분 cutoff
        """
        self.method = method
        self.window_size = window_size
        self.alpha = alpha
        self.min_cutoff = min_cutoff
        self.beta = beta
        self.d_cutoff = d_cutoff
        
        logger.debug(f"Smoother 초기화: method={method}, alpha={alpha}")
    
    def smooth(self, sequence: np.ndarray) -> np.ndarray:
        """
        시퀀스 스무딩 적용.
        
        Args:
            sequence: shape (T, NUM_KEYPOINTS, 3) [x, y, score]
            
        Returns:
            스무딩된 시퀀스 (동일 shape)
        """
        if self.method == "none":
            return sequence.copy()
        elif self.method == "moving_avg":
            return self._moving_average(sequence)
        elif self.method == "exponential":
            return self._exponential_ma(sequence)
        elif self.method == "one_euro":
            return self._one_euro_filter(sequence)
        elif self.method == "gaussian":
            return self._gaussian_smooth(sequence)
        else:
            logger.warning(f"Unknown smoothing method: {self.method}")
            return sequence.copy()
    
    def _moving_average(self, sequence: np.ndarray) -> np.ndarray:
        """이동 평균 스무딩"""
        result = sequence.copy()
        T = len(sequence)
        half_window = self.window_size // 2
        
        for t in range(T):
            start = max(0, t - half_window)
            end = min(T, t + half_window + 1)
            
            # x, y만 스무딩 (score는 유지)
            result[t, :, :2] = sequence[start:end, :, :2].mean(axis=0)
        
        return result
    
    def _exponential_ma(self, sequence: np.ndarray) -> np.ndarray:
        """지수 이동 평균 (EMA) 스무딩"""
        result = sequence.copy()
        T = len(sequence)
        
        for t in range(1, T):
            # x, y만 스무딩
            result[t, :, :2] = (
                self.alpha * sequence[t, :, :2] + 
                (1 - self.alpha) * result[t - 1, :, :2]
            )
        
        return result
    
    def _one_euro_filter(self, sequence: np.ndarray) -> np.ndarray:
        """
        One Euro Filter - 적응적 저역통과 필터.
        * 적응적 + 저역통과 필터(Low-Pass Filter)
        : 사람이 빨리 움직이면 필터를 약하게, 천천히 움직이면 필터를 세게 적용.
        
        빠른 움직임 → 덜 스무딩 (디테일 유지)
        느린 움직임 → 더 스무딩 (노이즈 제거)
        """
        result = sequence.copy()
        T = len(sequence)
        
        if T < 2:
            return result
        
        # 각 관절, 각 좌표별로 필터 적용
        for joint_idx in range(NUM_KEYPOINTS):
            for coord_idx in range(2):  # x, y만
                signal = sequence[:, joint_idx, coord_idx]
                result[:, joint_idx, coord_idx] = self._apply_one_euro_1d(signal)
        
        return result
    
    def _apply_one_euro_1d(self, signal: np.ndarray) -> np.ndarray:
        """1D 신호에 One Euro Filter 적용"""
        T = len(signal)
        result = np.zeros(T)
        result[0] = signal[0]
        
        # 미분 필터 상태
        dx_prev = 0.0
        
        for t in range(1, T):
            # 현재 미분 (속도)
            dx = signal[t] - signal[t - 1]
            
            # 미분 스무딩
            alpha_d = self._compute_alpha(self.d_cutoff)
            dx_hat = alpha_d * dx + (1 - alpha_d) * dx_prev
            dx_prev = dx_hat
            
            # 적응적 cutoff 계산
            cutoff = self.min_cutoff + self.beta * abs(dx_hat)
            alpha = self._compute_alpha(cutoff)
            
            # 신호 스무딩
            result[t] = alpha * signal[t] + (1 - alpha) * result[t - 1]
        
        return result
    
    def _compute_alpha(self, cutoff: float, rate: float = DEFAULT_ONE_EURO_RATE) -> float:
        """cutoff 주파수로부터 alpha 계산"""
        tau = 1.0 / (2.0 * np.pi * cutoff)
        te = 1.0 / rate
        return 1.0 / (1.0 + tau / te)
    
    def _gaussian_smooth(self, sequence: np.ndarray) -> np.ndarray:
        """가우시안 커널 스무딩"""
        from scipy.ndimage import gaussian_filter1d
        
        result = sequence.copy()
        sigma = self.window_size / GAUSSIAN_SIGMA_FACTOR  # 대략적인 sigma
        
        for joint_idx in range(NUM_KEYPOINTS):
            for coord_idx in range(2):
                result[:, joint_idx, coord_idx] = gaussian_filter1d(
                    sequence[:, joint_idx, coord_idx],
                    sigma=sigma,
                    mode='nearest'
                )
        
        return result


class PoseNormalizer:
    """
    자세 데이터 정규화기.
    
    시퀀스 데이터를 정규화하여 체형/거리 차이를 보정합니다.
    
    Attributes:
        reference_height: 정규화 기준 높이
        fallback_scale: 스케일 계산 실패 시 대체값
        
    Example:
        >>> normalizer = PoseNormalizer()
        >>> normalized = normalizer.normalize_sequence(sequence, method="torso")
    """
    
    # 정규화에 사용할 필수 키포인트
    REQUIRED_KEYPOINTS = {
        "torso": [
            KeypointIndex.L_SHOULDER, KeypointIndex.R_SHOULDER,
            KeypointIndex.L_HIP, KeypointIndex.R_HIP
        ],
        "hip_center": [KeypointIndex.L_HIP, KeypointIndex.R_HIP]
    }
    
    def __init__(
        self,
        reference_height: Optional[float] = None,
        fallback_scale: float = DEFAULT_FALLBACK_SCALE
    ):
        """
        PoseNormalizer 초기화.
        
        Args:
            reference_height: 정규화 기준 높이 (None이면 설정값 사용)
            fallback_scale: 스케일 계산 실패 시 대체값
        """
        self.reference_height = reference_height or settings.REFERENCE_HEIGHT
        self.fallback_scale = fallback_scale
        
        logger.info(
            f"PoseNormalizer 초기화: reference_height={self.reference_height}"
        )
    
    def normalize_sequence(
        self,
        sequence: np.ndarray,
        method: Optional[NormalizationMethod] = None
    ) -> np.ndarray:
        """
        관절 시퀀스 정규화.
        
        Args:
            sequence: 입력 시퀀스 shape (T, NUM_KEYPOINTS, 3) [x, y, score]
            method: 정규화 방법 (None이면 설정값 사용)
            
        Returns:
            정규화된 시퀀스 (동일 shape)
            
        Raises:
            NormalizationError: 정규화 실패
            ValueError: 잘못된 method 값
        """
        method = method or settings.NORMALIZATION_METHOD
        
        self._validate_sequence(sequence)
        
        if method == "torso":
            return self._normalize_by_torso(sequence)
        elif method == "bbox":
            return self._normalize_by_bbox(sequence)
        elif method == "hip_center":
            return self._normalize_by_hip_center(sequence)
        else:
            raise ValueError(f"Unknown normalization method: {method}")
    
    def _validate_sequence(self, sequence: np.ndarray) -> None:
        """
        시퀀스 유효성 검사.
        
        Args:
            sequence: 검사할 시퀀스
            
        Raises:
            NormalizationError: 유효하지 않은 시퀀스
        """
        if sequence is None or len(sequence) == 0:
            raise NormalizationError("시퀀스가 비어있습니다")
        
        if sequence.ndim != 3:
            raise NormalizationError(
                f"시퀀스 차원이 잘못되었습니다: {sequence.ndim}D (expected 3D)",
                details={"shape": sequence.shape}
            )
        
        if sequence.shape[1] != NUM_KEYPOINTS or sequence.shape[2] != 3:
            raise NormalizationError(
                f"시퀀스 형태가 잘못되었습니다: {sequence.shape} (expected (T, {NUM_KEYPOINTS}, 3))",
                details={"shape": sequence.shape}
            )
    
    def _normalize_by_torso(self, sequence: np.ndarray) -> np.ndarray:
        """
        몸통(어깨-골반) 기준 정규화.
        
        중심: 골반 중앙
        스케일: 어깨 중앙 ~ 골반 중앙 거리
        
        Args:
            sequence: 입력 시퀀스
            
        Returns:
            정규화된 시퀀스
        """
        result = sequence.copy()
        
        # 기준 스케일 계산 (전체 시퀀스 평균)
        reference_scale = self._compute_average_torso_length(sequence)
        
        for i in range(len(sequence)):
            frame = sequence[i]
            
            # 기준점 추출
            l_shoulder = frame[KeypointIndex.L_SHOULDER, :2]
            r_shoulder = frame[KeypointIndex.R_SHOULDER, :2]
            l_hip = frame[KeypointIndex.L_HIP, :2]
            r_hip = frame[KeypointIndex.R_HIP, :2]
            
            # 점수 확인
            scores = frame[self.REQUIRED_KEYPOINTS["torso"], 2]
            
            if np.all(scores > settings.MIN_KEYPOINT_SCORE):
                # 중심점: 골반 중앙
                hip_center = (l_hip + r_hip) / 2
                
                # 스케일: 어깨-골반 거리
                shoulder_center = (l_shoulder + r_shoulder) / 2
                torso_length = np.linalg.norm(shoulder_center - hip_center)
                
                # 스케일이 너무 작으면 참조값 사용
                if torso_length < EPSILON:
                    torso_length = reference_scale
                
                # 정규화 적용
                result[i, :, :2] = (
                    (frame[:, :2] - hip_center) / torso_length * self.reference_height
                )
            else:
                # 기준점이 없으면 이전 프레임 기준 또는 스킵
                if i > 0:
                    # 이전 프레임과 동일한 변환 적용
                    result[i, :, :2] = result[i - 1, :, :2]
                    result[i, :, 2] = 0.0  # 신뢰도 0으로 표시
        
        return result
    
    def _normalize_by_hip_center(self, sequence: np.ndarray) -> np.ndarray:
        """
        골반 중앙 기준 위치 정규화 (스케일 유지).
        
        Args:
            sequence: 입력 시퀀스
            
        Returns:
            정규화된 시퀀스
        """
        result = sequence.copy()
        
        for i in range(len(sequence)):
            frame = sequence[i]
            
            l_hip = frame[KeypointIndex.L_HIP, :2]
            r_hip = frame[KeypointIndex.R_HIP, :2]
            scores = frame[[KeypointIndex.L_HIP, KeypointIndex.R_HIP], 2]
            
            if np.all(scores > settings.MIN_KEYPOINT_SCORE):
                hip_center = (l_hip + r_hip) / 2
                result[i, :, :2] = frame[:, :2] - hip_center
            elif i > 0:
                # 이전 프레임 값 유지
                result[i] = result[i - 1]
                result[i, :, 2] = 0.0
        
        return result
    
    def _normalize_by_bbox(self, sequence: np.ndarray) -> np.ndarray:
        """
        바운딩 박스 기준 정규화 (0~1 범위).
        
        Args:
            sequence: 입력 시퀀스
            
        Returns:
            정규화된 시퀀스
        """
        result = sequence.copy()
        
        for i in range(len(sequence)):
            frame = sequence[i]
            valid_mask = frame[:, 2] > settings.MIN_KEYPOINT_SCORE
            valid_points = frame[valid_mask, :2]
            
            if len(valid_points) < 2:
                if i > 0:
                    result[i] = result[i - 1]
                    result[i, :, 2] = 0.0
                continue
            
            min_xy = valid_points.min(axis=0)
            max_xy = valid_points.max(axis=0)
            bbox_size = max_xy - min_xy
            
            # 0 방지
            bbox_size = np.where(bbox_size < EPSILON, 1.0, bbox_size)
            
            result[i, :, :2] = (frame[:, :2] - min_xy) / bbox_size
        
        return result
    
    def _compute_average_torso_length(self, sequence: np.ndarray) -> float:
        """
        시퀀스 전체의 평균 몸통 길이 계산.
        
        Args:
            sequence: 입력 시퀀스
            
        Returns:
            평균 몸통 길이 (유효한 프레임 없으면 fallback_scale)
        """
        lengths = []
        
        for frame in sequence:
            scores = frame[self.REQUIRED_KEYPOINTS["torso"], 2]
            
            if np.all(scores > settings.MIN_KEYPOINT_SCORE):
                l_shoulder = frame[KeypointIndex.L_SHOULDER, :2]
                r_shoulder = frame[KeypointIndex.R_SHOULDER, :2]
                l_hip = frame[KeypointIndex.L_HIP, :2]
                r_hip = frame[KeypointIndex.R_HIP, :2]
                
                shoulder_center = (l_shoulder + r_shoulder) / 2
                hip_center = (l_hip + r_hip) / 2
                length = np.linalg.norm(shoulder_center - hip_center)
                
                if length > EPSILON:
                    lengths.append(length)
        
        if lengths:
            return float(np.median(lengths))
        else:
            logger.warning(
                f"유효한 몸통 길이를 계산할 수 없습니다. "
                f"fallback_scale={self.fallback_scale} 사용"
            )
            return self.fallback_scale
    
    # =========================================================================
    # Phase 1: 부모/아이 구분 (강건한 2-pass + IoU 트래킹 + 스왑 감지)
    # =========================================================================
    
    def identify_persons(
        self,
        frames_data: list["FramePoseData"],
        method: str = "torso_length",
        use_robust_tracking: bool = True,
        swap_detection: bool = True,
        iou_threshold: float = DEFAULT_IOU_THRESHOLD,
        swap_window_size: int = DEFAULT_SWAP_WINDOW
    ) -> list[FramePersons]:
        """
        프레임별로 부모/아이를 구분합니다 (강건한 2-pass + IoU 트래킹 + 스왑 감지).
        
        Args:
            frames_data: PoseExtractor 결과
            method: 구분 방법 ("torso_length", "bbox_size", "combined")
            use_robust_tracking: IoU 기반 강건 트래킹 사용 여부
            swap_detection: 스왑 감지 및 수정 활성화 여부
            iou_threshold: IoU 트래킹 임계값
            swap_window_size: 스왑 감지 윈도우 크기
            
        Returns:
            역할이 할당된 FramePersons 리스트
        """
        if not frames_data:
            return []
        
        # =====================================================================
        # PASS 1: 전체 통계 수집 및 클러스터 기준값 계산
        # =====================================================================
        all_features = []
        for frame in frames_data:
            for person in frame.persons:
                torso = self._compute_person_torso_length(person)
                height = self._compute_skeleton_height(person)
                bbox_area = person.bbox[2] * person.bbox[3] if len(person.bbox) >= 4 else 0
                
                all_features.append({
                    "frame_idx": frame.frame_idx,
                    "person": person,
                    "torso_length": torso,
                    "skeleton_height": height,
                    "bbox_area": bbox_area,
                    "bbox": person.bbox
                })
        
        if not all_features:
            return [FramePersons(frame_idx=f.frame_idx, num_detected=0) for f in frames_data]
        
        # 전체 torso 값으로 클러스터 기준점 계산
        all_torsos = [f["torso_length"] for f in all_features if f["torso_length"] > 0]
        
        if not all_torsos:
            return [FramePersons(frame_idx=f.frame_idx, num_detected=0) for f in frames_data]
        
        # 중앙값을 기준으로 부모/아이 클러스터 분리
        median_torso = np.median(all_torsos)
        parent_torsos = [t for t in all_torsos if t >= median_torso]
        child_torsos = [t for t in all_torsos if t < median_torso]
        
        # 각 클러스터의 평균값 (글로벌 기준점)
        global_parent_avg = np.mean(parent_torsos) if parent_torsos else median_torso
        global_child_avg = np.mean(child_torsos) if child_torsos else median_torso * CHILD_TORSO_RATIO_FALLBACK
        
        logger.debug(
            f"글로벌 통계: median={median_torso:.1f}, "
            f"parent_avg={global_parent_avg:.1f}, child_avg={global_child_avg:.1f}"
        )
        
        # =====================================================================
        # PASS 2: IoU 기반 트래킹 + 역할 할당
        # =====================================================================
        result = []
        prev_frame_persons: Optional[FramePersons] = None
        
        for frame in frames_data:
            if not frame.persons:
                result.append(FramePersons(frame_idx=frame.frame_idx, num_detected=0))
                continue
            
            # 각 사람의 IdentifiedPerson 생성
            identified = []
            for person in frame.persons:
                torso = self._compute_person_torso_length(person)
                height = self._compute_skeleton_height(person)
                bbox_area = person.bbox[2] * person.bbox[3] if len(person.bbox) >= 4 else 0
                
                identified.append(IdentifiedPerson(
                    person_pose=person,
                    role=PersonRole.UNKNOWN,
                    torso_length=torso,
                    skeleton_height=height,
                    bbox_area=bbox_area,
                    role_confidence=0.0
                ))
            
            # 역할 할당
            if len(identified) == 1:
                # 한 명만 있으면 글로벌 기준으로 역할 결정
                single = identified[0]
                dist_to_parent = abs(single.torso_length - global_parent_avg)
                dist_to_child = abs(single.torso_length - global_child_avg)
                
                if dist_to_parent < dist_to_child:
                    single.role = PersonRole.PARENT
                    single.role_confidence = CONF_SINGLE_ROLE
                    result.append(FramePersons(
                        frame_idx=frame.frame_idx,
                        parent=single,
                        child=None,
                        num_detected=1
                    ))
                else:
                    single.role = PersonRole.CHILD
                    single.role_confidence = CONF_SINGLE_ROLE
                    result.append(FramePersons(
                        frame_idx=frame.frame_idx,
                        child=single,
                        parent=None,
                        num_detected=1
                    ))
            elif len(identified) >= 2:
                # 두 명 이상: IoU 트래킹 또는 글로벌 기준 사용
                if use_robust_tracking and prev_frame_persons is not None:
                    parent_candidate, child_candidate = self._assign_roles_with_iou(
                        identified, prev_frame_persons, 
                        global_parent_avg, global_child_avg,
                        iou_threshold, method
                    )
                else:
                    # 첫 프레임 또는 트래킹 미사용: 글로벌 기준 사용
                    parent_candidate, child_candidate = self._assign_roles_by_global(
                        identified, global_parent_avg, global_child_avg, method
                    )
                
                frame_result = FramePersons(
                    frame_idx=frame.frame_idx,
                    parent=parent_candidate,
                    child=child_candidate,
                    num_detected=len(identified)
                )
                result.append(frame_result)
                prev_frame_persons = frame_result
            else:
                result.append(FramePersons(frame_idx=frame.frame_idx, num_detected=0))
                
            # prev_frame_persons 업데이트
            if result[-1].parent or result[-1].child:
                prev_frame_persons = result[-1]
        
        # =====================================================================
        # PASS 3: 스왑 감지 및 수정 (후처리)
        # =====================================================================
        if swap_detection and len(result) > swap_window_size:
            self._detect_and_fix_swaps(result, swap_window_size)
        
        # 통계 로깅
        parent_count = sum(1 for fp in result if fp.parent is not None)
        child_count = sum(1 for fp in result if fp.child is not None)
        logger.info(
            f"역할 구분 완료: {len(result)}프레임, "
            f"부모 감지={parent_count}, 아이 감지={child_count}"
        )
        
        return result
    
    def _assign_roles(
        self,
        persons: list[IdentifiedPerson],
        method: str,
        prev_parent_id: Optional[int],
        prev_child_id: Optional[int]
    ) -> tuple[Optional[IdentifiedPerson], Optional[IdentifiedPerson]]:
        """두 사람에게 부모/아이 역할 할당"""
        
        if len(persons) < 2:
            if persons:
                persons[0].role = PersonRole.CHILD
                return None, persons[0]
            return None, None
        
        # 정렬 기준 결정
        if method == "torso_length":
            sorted_persons = sorted(persons, key=lambda p: p.torso_length, reverse=True)
        elif method == "bbox_size":
            sorted_persons = sorted(persons, key=lambda p: p.bbox_area, reverse=True)
        else:  # combined
            sorted_persons = sorted(
                persons, 
                key=lambda p: p.torso_length * COMBINED_TORSO_WEIGHT + p.bbox_area * COMBINED_BBOX_WEIGHT,
                reverse=True
            )
        
        # 시간적 일관성 체크
        if prev_parent_id is not None:
            for p in sorted_persons:
                if p.person_pose.person_id == prev_parent_id:
                    # 이전 프레임의 부모를 찾음
                    parent = p
                    parent.role = PersonRole.PARENT
                    parent.role_confidence = CONF_PREV_MATCH
                    
                    # 나머지 중 가장 작은 것을 아이로
                    others = [x for x in sorted_persons if x != parent]
                    if others:
                        child = min(others, key=lambda x: x.torso_length)
                        child.role = PersonRole.CHILD
                        child.role_confidence = CONF_PREV_MATCH
                        return parent, child
                    return parent, None
        
        # 새로 할당: 가장 큰 사람 = 부모, 가장 작은 사람 = 아이
        parent = sorted_persons[0]
        parent.role = PersonRole.PARENT
        parent.role_confidence = CONF_NEW_MATCH
        
        child = sorted_persons[-1]  # 가장 작은 사람
        child.role = PersonRole.CHILD
        child.role_confidence = CONF_NEW_MATCH
        
        # 차이가 작으면 신뢰도 낮춤
        if parent.torso_length > 0 and child.torso_length > 0:
            ratio = parent.torso_length / child.torso_length
            if ratio < ROLE_DIFFERENCE_RATIO_THRESHOLD:  # 차이가 부족하면
                parent.role_confidence = CONF_LOW
                child.role_confidence = CONF_LOW
        
        return parent, child
    
    def _assign_roles_by_global(
        self,
        persons: list[IdentifiedPerson],
        global_parent_avg: float,
        global_child_avg: float,
        method: str
    ) -> tuple[Optional[IdentifiedPerson], Optional[IdentifiedPerson]]:
        """글로벌 통계 기준으로 역할 할당 (첫 프레임 또는 트래킹 실패 시)"""
        
        if len(persons) < 2:
            if persons:
                persons[0].role = PersonRole.CHILD
                persons[0].role_confidence = CONF_SINGLE_ROLE
                return None, persons[0]
            return None, None
        
        # 각 사람별로 글로벌 기준과의 거리 계산
        for p in persons:
            p._dist_to_parent = abs(p.torso_length - global_parent_avg)
            p._dist_to_child = abs(p.torso_length - global_child_avg)
        
        # 가장 부모에 가까운 사람 찾기
        parent = min(persons, key=lambda p: p._dist_to_parent)
        parent.role = PersonRole.PARENT
        parent.role_confidence = CONF_GLOBAL_MATCH
        
        # 나머지 중 가장 아이에 가까운 사람 찾기
        others = [p for p in persons if p != parent]
        child = min(others, key=lambda p: p._dist_to_child)
        child.role = PersonRole.CHILD
        child.role_confidence = CONF_GLOBAL_MATCH
        
        return parent, child
    
    def _assign_roles_with_iou(
        self,
        curr_persons: list[IdentifiedPerson],
        prev_frame: FramePersons,
        global_parent_avg: float,
        global_child_avg: float,
        iou_threshold: float,
        method: str
    ) -> tuple[Optional[IdentifiedPerson], Optional[IdentifiedPerson]]:
        """IoU 기반 트래킹으로 역할 할당"""
        
        if len(curr_persons) < 2:
            return self._assign_roles_by_global(
                curr_persons, global_parent_avg, global_child_avg, method
            )
        
        parent_candidate = None
        child_candidate = None
        matched_indices = set()
        
        # 이전 프레임의 부모와 매칭 시도
        if prev_frame.parent:
            prev_parent_bbox = prev_frame.parent.person_pose.bbox
            best_iou = 0
            best_idx = None
            
            for idx, curr in enumerate(curr_persons):
                iou = self._compute_iou(prev_parent_bbox, curr.person_pose.bbox)
                if iou > best_iou and iou > iou_threshold:
                    best_iou = iou
                    best_idx = idx
            
            if best_idx is not None:
                parent_candidate = curr_persons[best_idx]
                parent_candidate.role = PersonRole.PARENT
                parent_candidate.role_confidence = CONF_IOU_MATCH_BASE + best_iou * CONF_IOU_MATCH_WEIGHT  # IoU 반영
                matched_indices.add(best_idx)
        
        # 이전 프레임의 아이와 매칭 시도
        if prev_frame.child:
            prev_child_bbox = prev_frame.child.person_pose.bbox
            best_iou = 0
            best_idx = None
            
            for idx, curr in enumerate(curr_persons):
                if idx in matched_indices:
                    continue
                iou = self._compute_iou(prev_child_bbox, curr.person_pose.bbox)
                if iou > best_iou and iou > iou_threshold:
                    best_iou = iou
                    best_idx = idx
            
            if best_idx is not None:
                child_candidate = curr_persons[best_idx]
                child_candidate.role = PersonRole.CHILD
                child_candidate.role_confidence = CONF_IOU_MATCH_BASE + best_iou * CONF_IOU_MATCH_WEIGHT
                matched_indices.add(best_idx)
        
        # 매칭 실패 시 글로벌 기준 사용
        if parent_candidate is None or child_candidate is None:
            unmatched = [p for i, p in enumerate(curr_persons) if i not in matched_indices]
            
            if parent_candidate is None and unmatched:
                # 글로벌 부모 평균과 가장 가까운 사람
                parent_candidate = min(unmatched, key=lambda p: abs(p.torso_length - global_parent_avg))
                parent_candidate.role = PersonRole.PARENT
                parent_candidate.role_confidence = CONF_UNMATCHED_GLOBAL
                unmatched.remove(parent_candidate)
            
            if child_candidate is None and unmatched:
                # 글로벌 아이 평균과 가장 가까운 사람
                child_candidate = min(unmatched, key=lambda p: abs(p.torso_length - global_child_avg))
                child_candidate.role = PersonRole.CHILD
                child_candidate.role_confidence = CONF_UNMATCHED_GLOBAL
        
        return parent_candidate, child_candidate
    
    def _compute_iou(self, bbox1: list, bbox2: list) -> float:
        """두 바운딩 박스의 IoU(Intersection over Union) 계산.
        
        Args:
            bbox1, bbox2: [cx, cy, w, h] 형식
            
        Returns:
            IoU 값 (0~1)
        """
        if len(bbox1) < 4 or len(bbox2) < 4:
            return 0.0
        
        # [cx, cy, w, h] -> [x1, y1, x2, y2]
        x1_min = bbox1[0] - bbox1[2] / 2
        y1_min = bbox1[1] - bbox1[3] / 2
        x1_max = bbox1[0] + bbox1[2] / 2
        y1_max = bbox1[1] + bbox1[3] / 2
        
        x2_min = bbox2[0] - bbox2[2] / 2
        y2_min = bbox2[1] - bbox2[3] / 2
        x2_max = bbox2[0] + bbox2[2] / 2
        y2_max = bbox2[1] + bbox2[3] / 2
        
        # 교집합 계산
        inter_x = max(0, min(x1_max, x2_max) - max(x1_min, x2_min))
        inter_y = max(0, min(y1_max, y2_max) - max(y1_min, y2_min))
        intersection = inter_x * inter_y
        
        # 합집합 계산
        area1 = bbox1[2] * bbox1[3]
        area2 = bbox2[2] * bbox2[3]
        union = area1 + area2 - intersection
        
        return intersection / union if union > 0 else 0.0
    
    def _detect_and_fix_swaps(
        self,
        frame_persons: list[FramePersons],
        window_size: int = 5
    ) -> None:
        """역할 스왑 감지 및 수정 (후처리).
        
        연속된 프레임에서 갑자기 역할이 뒤바뀌는 경우를 감지하고 수정합니다.
        
        Args:
            frame_persons: 역할이 할당된 프레임 리스트 (in-place 수정)
            window_size: 비교 윈도우 크기
        """
        swap_count = 0
        
        for i in range(window_size, len(frame_persons)):
            curr = frame_persons[i]
            
            # 현재 프레임에 부모와 아이가 모두 있어야 검사
            if not curr.parent or not curr.child:
                continue
            
            # 이전 window_size 프레임의 부모/아이 평균 torso 계산
            prev_parent_torsos = []
            prev_child_torsos = []
            
            for j in range(max(0, i - window_size), i):
                fp = frame_persons[j]
                if fp.parent and fp.parent.torso_length > 0:
                    prev_parent_torsos.append(fp.parent.torso_length)
                if fp.child and fp.child.torso_length > 0:
                    prev_child_torsos.append(fp.child.torso_length)
            
            # 충분한 이력이 없으면 스킵
            if len(prev_parent_torsos) < 2 or len(prev_child_torsos) < 2:
                continue
            
            avg_parent = np.mean(prev_parent_torsos)
            avg_child = np.mean(prev_child_torsos)
            
            curr_parent_t = curr.parent.torso_length
            curr_child_t = curr.child.torso_length
            
            # 정상 배치 vs 스왑 배치의 거리 비교
            dist_normal = abs(curr_parent_t - avg_parent) + abs(curr_child_t - avg_child)
            dist_swapped = abs(curr_parent_t - avg_child) + abs(curr_child_t - avg_parent)
            
            # 스왑이 더 자연스러우면 (THRESHOLD 비율 이상 가까우면) 교환
            if dist_swapped < dist_normal * SWAP_DISTANCE_THRESHOLD_RATIO:
                # 역할 교환
                curr.parent, curr.child = curr.child, curr.parent
                curr.parent.role = PersonRole.PARENT
                curr.child.role = PersonRole.CHILD
                curr.parent.role_confidence = CONF_SWAP_FIX
                curr.child.role_confidence = CONF_SWAP_FIX
                swap_count += 1
        
        if swap_count > 0:
            logger.info(f"스왑 감지/수정: {swap_count}개 프레임 교정됨")

    def _compute_person_torso_length(self, person: "PersonPose") -> float:
        """PersonPose에서 torso 길이 계산"""
        keypoints = person.keypoints
        
        # keypoints 키 형식: "L_Shoulder", "R_Shoulder", "L_Hip", "R_Hip"
        # 또는 "left_shoulder", "right_shoulder" 등 다양한 형식 지원
        key_mapping = {
            "left_shoulder": ["L_Shoulder", "left_shoulder", "LeftShoulder"],
            "right_shoulder": ["R_Shoulder", "right_shoulder", "RightShoulder"],
            "left_hip": ["L_Hip", "left_hip", "LeftHip"],
            "right_hip": ["R_Hip", "right_hip", "RightHip"]
        }
        
        def find_keypoint(target):
            for key in key_mapping.get(target, [target]):
                if key in keypoints:
                    return keypoints[key]
            return None
        
        l_shoulder_kp = find_keypoint("left_shoulder")
        r_shoulder_kp = find_keypoint("right_shoulder")
        l_hip_kp = find_keypoint("left_hip")
        r_hip_kp = find_keypoint("right_hip")
        
        if not all([l_shoulder_kp, r_shoulder_kp, l_hip_kp, r_hip_kp]):
            return 0.0
        
        # 신뢰도 체크
        min_score = settings.MIN_KEYPOINT_SCORE
        all_kps = [l_shoulder_kp, r_shoulder_kp, l_hip_kp, r_hip_kp]
        if any(kp.get("score", 0) < min_score for kp in all_kps):
            return 0.0
        
        l_shoulder = np.array([l_shoulder_kp["x"], l_shoulder_kp["y"]])
        r_shoulder = np.array([r_shoulder_kp["x"], r_shoulder_kp["y"]])
        l_hip = np.array([l_hip_kp["x"], l_hip_kp["y"]])
        r_hip = np.array([r_hip_kp["x"], r_hip_kp["y"]])
        
        shoulder_center = (l_shoulder + r_shoulder) / 2
        hip_center = (l_hip + r_hip) / 2
        
        return float(np.linalg.norm(shoulder_center - hip_center))
    
    def _compute_skeleton_height(self, person: "PersonPose") -> float:
        """스켈레톤 전체 높이 (머리 ~ 발목) 계산"""
        keypoints = person.keypoints
        
        y_coords = []
        for name, kp in keypoints.items():
            if kp.get("score", 0) > settings.MIN_KEYPOINT_SCORE:
                y_coords.append(kp["y"])
        
        if len(y_coords) < 2:
            return 0.0
        
        return float(max(y_coords) - min(y_coords))
    
    # =========================================================================
    # Phase 2: 다중 객체 정규화
    # =========================================================================
    
    def normalize_multi_person(
        self,
        frame_persons: list[FramePersons],
        method: NormalizationMethod = "torso"
    ) -> MultiPersonResult:
        """
        부모와 아이 각각 정규화된 시퀀스 반환.
        
        Args:
            frame_persons: identify_persons() 결과
            method: 정규화 방법
            
        Returns:
            MultiPersonResult (parent_sequence, child_sequence 등)
        """
        T = len(frame_persons)
        
        # Raw 시퀀스 추출
        parent_raw = np.zeros((T, NUM_KEYPOINTS, 3))
        child_raw = np.zeros((T, NUM_KEYPOINTS, 3))
        
        parent_torsos = []
        child_torsos = []
        
        for i, fp in enumerate(frame_persons):
            if fp.parent is not None:
                parent_raw[i] = fp.parent.to_array()
                if fp.parent.torso_length > 0:
                    parent_torsos.append(fp.parent.torso_length)
            
            if fp.child is not None:
                child_raw[i] = fp.child.to_array()
                if fp.child.torso_length > 0:
                    child_torsos.append(fp.child.torso_length)
        
        # 평균 torso 길이 계산
        parent_avg_torso = float(np.median(parent_torsos)) if parent_torsos else None
        child_avg_torso = float(np.median(child_torsos)) if child_torsos else self.fallback_scale
        
        # 정규화 수행
        has_parent = any(fp.parent is not None for fp in frame_persons)
        
        if has_parent and parent_avg_torso:
            parent_sequence = self._normalize_with_custom_scale(
                parent_raw, parent_avg_torso, method
            )
        else:
            parent_sequence = None
        
        child_sequence = self._normalize_with_custom_scale(
            child_raw, child_avg_torso, method
        )
        
        return MultiPersonResult(
            parent_sequence=parent_sequence,
            child_sequence=child_sequence,
            parent_raw=parent_raw if has_parent else None,
            child_raw=child_raw,
            frame_persons=frame_persons,
            parent_avg_torso=parent_avg_torso,
            child_avg_torso=child_avg_torso
        )
    
    def _normalize_with_custom_scale(
        self,
        sequence: np.ndarray,
        torso_length: float,
        method: NormalizationMethod
    ) -> np.ndarray:
        """지정된 torso 길이 기준으로 정규화"""
        result = sequence.copy()
        
        for i in range(len(sequence)):
            frame = sequence[i]
            
            # 유효한 프레임인지 확인
            if frame[:, 2].max() < settings.MIN_KEYPOINT_SCORE:
                # 이전 프레임 복사
                if i > 0:
                    result[i, :, :2] = result[i - 1, :, :2]
                    result[i, :, 2] = 0.0
                continue
            
            # 골반 중심 계산
            l_hip = frame[KeypointIndex.L_HIP, :2]
            r_hip = frame[KeypointIndex.R_HIP, :2]
            hip_center = (l_hip + r_hip) / 2
            
            # 정규화 적용
            if method == "torso":
                scale = torso_length if torso_length > EPSILON else self.fallback_scale
                result[i, :, :2] = (frame[:, :2] - hip_center) / scale * self.reference_height
            elif method == "hip_center":
                result[i, :, :2] = frame[:, :2] - hip_center
            elif method == "bbox":
                valid_mask = frame[:, 2] > settings.MIN_KEYPOINT_SCORE
                if valid_mask.sum() >= 2:
                    valid_points = frame[valid_mask, :2]
                    min_xy = valid_points.min(axis=0)
                    max_xy = valid_points.max(axis=0)
                    bbox_size = max_xy - min_xy
                    bbox_size = np.where(bbox_size < EPSILON, 1.0, bbox_size)
                    result[i, :, :2] = (frame[:, :2] - min_xy) / bbox_size
        
        return result
    
    # =========================================================================
    # Phase 3: Smoothing 통합
    # =========================================================================
    
    def smooth_sequence(
        self,
        sequence: np.ndarray,
        method: SmoothingMethod = "exponential",
        **kwargs
    ) -> np.ndarray:
        """
        시퀀스에 스무딩 적용.
        
        Args:
            sequence: 입력 시퀀스 (T, NUM_KEYPOINTS, 3)
            method: 스무딩 방법
            **kwargs: Smoother 추가 파라미터
            
        Returns:
            스무딩된 시퀀스
        """
        smoother = Smoother(method=method, **kwargs)
        return smoother.smooth(sequence)
    
    # =========================================================================
    # 통합 API
    # =========================================================================
    
    def normalize_and_smooth(
        self,
        frames_data: list["FramePoseData"],
        identify_roles: bool = True,
        smooth: bool = True,
        smooth_method: SmoothingMethod = "exponential",
        normalization_method: NormalizationMethod = "torso",
        smooth_kwargs: Optional[dict] = None
    ) -> dict:
        """
        완전한 정규화 파이프라인 (역할 구분 + 정규화 + 스무딩).
        
        Args:
            frames_data: PoseExtractor 결과
            identify_roles: 부모/아이 구분 수행 여부
            smooth: 스무딩 적용 여부
            smooth_method: 스무딩 방법
            normalization_method: 정규화 방법
            smooth_kwargs: Smoother 추가 파라미터
            
        Returns:
            {
                "parent_sequence": np.ndarray or None,
                "child_sequence": np.ndarray,
                "parent_raw": np.ndarray or None,
                "child_raw": np.ndarray,
                "frame_persons": list[FramePersons],
                "metadata": {...}
            }
        """
        smooth_kwargs = smooth_kwargs or {}
        
        if identify_roles:
            # 1. 부모/아이 구분
            frame_persons = self.identify_persons(frames_data, method="torso_length")
            
            # 2. 다중 객체 정규화
            multi_result = self.normalize_multi_person(
                frame_persons, 
                method=normalization_method
            )
            
            parent_seq = multi_result.parent_sequence
            child_seq = multi_result.child_sequence
            parent_raw = multi_result.parent_raw
            child_raw = multi_result.child_raw
        else:
            # 기존 방식: 가장 큰 bbox 기준 단일 인물
            from app.pipeline.pose_extractor import PoseExtractor
            extractor = PoseExtractor()
            raw_sequence = extractor.get_main_person_sequence(frames_data)
            
            child_raw = raw_sequence
            child_seq = self.normalize_sequence(raw_sequence, method=normalization_method)
            parent_seq = None
            parent_raw = None
            frame_persons = []
            multi_result = None
        
        # 3. 스무딩 적용
        if smooth:
            smoother = Smoother(method=smooth_method, **smooth_kwargs)
            child_seq = smoother.smooth(child_seq)
            if parent_seq is not None:
                parent_seq = smoother.smooth(parent_seq)
        
        # 4. 결과 구성
        metadata = {
            "total_frames": len(frames_data),
            "identify_roles": identify_roles,
            "smooth": smooth,
            "smooth_method": smooth_method if smooth else None,
            "normalization_method": normalization_method
        }
        
        if multi_result:
            metadata.update({
                "parent_avg_torso": multi_result.parent_avg_torso,
                "child_avg_torso": multi_result.child_avg_torso,
                "parent_detected_frames": sum(1 for fp in frame_persons if fp.parent),
                "child_detected_frames": sum(1 for fp in frame_persons if fp.child)
            })
        
        return {
            "parent_sequence": parent_seq,
            "child_sequence": child_seq,
            "parent_raw": parent_raw,
            "child_raw": child_raw,
            "frame_persons": frame_persons,
            "metadata": metadata
        }