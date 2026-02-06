# AI/services/pose-estimation/app/pipeline/similarity.py
"""
동작 유사도 계산 모듈.

정렬된 두 시퀀스 간의 유사도를 프레임별, 부위별로 계산합니다.
동작 특성에 따라 부위별 가중치를 다르게 적용할 수 있습니다.

[전처리 요구사항]
- 이 모듈은 입력 좌표가 정규화(Normalization)되어 있다고 가정합니다.
- 정규화되지 않은 픽셀 좌표는 PoseNormalizer를 통해 사전 처리 필수입니다.
- DTWAligner를 통해 시퀀스 길이가 정렬되어 있어야 합니다.

[유사도 계산 방식]
- 유클리드 거리 역수: similarity = 1 / (1 + distance)
- 좌표가 완벽히 일치하면 거리 0 → 유사도 1.0
"""

import numpy as np
import logging
from typing import Optional
from dataclasses import dataclass, field

from app.config import settings
from app.pipeline.exceptions import SimilarityError
from app.pipeline.pose_extractor import KeypointIndex

logger = logging.getLogger(__name__)

# =============================================================================
# 상수 (하드코딩 제거)
# =============================================================================
EPSILON = 1e-8                     # 0 나눗셈 방지
MIN_VALID_KEYPOINTS = 2            # 부위별 최소 유효 키포인트 수
SIMILARITY_FLOOR = 0.0             # 유사도 최소값
DEFAULT_INVALID_SIMILARITY = 0.0   # 유효하지 않은 프레임의 유사도

# 디버그/모니터링 관련
DEBUG_LOG_SAMPLE_FRAMES = 5        # 샘플 로깅할 프레임 수
DEBUG_LOG_INTERVAL = 10            # N 프레임마다 로깅


class ActionWeightPresets:
    """
    동작별 최적 가중치 프리셋.
    
    동작 특성에 맞는 부위별 가중치를 제공합니다.
    
    Example:
        >>> weights = ActionWeightPresets.get("hurray")
        >>> calculator = SimilarityCalculator(**weights)
    """
    
    PRESETS = {
        "hurray": {
            "upper_body_weight": 2.0,   # 팔 위로 올리기 중요
            "lower_body_weight": 0.5,   # 하체 덜 중요
            "head_weight": 0.3
        },
        "clapping": {
            "upper_body_weight": 2.5,   # 손 위치 매우 중요
            "lower_body_weight": 0.3,
            "head_weight": 0.2
        },
        "jumping": {
            "upper_body_weight": 1.0,
            "lower_body_weight": 2.0,   # 다리 동작 중요
            "head_weight": 0.5
        },
        "waving": {
            "upper_body_weight": 2.2,   # 손 흔들기
            "lower_body_weight": 0.3,
            "head_weight": 0.3
        },
        "pointing": {
            "upper_body_weight": 2.0,   # 팔/손 위치 중요
            "lower_body_weight": 0.5,
            "head_weight": 0.5
        },
        "default": {
            "upper_body_weight": 1.5,
            "lower_body_weight": 1.0,
            "head_weight": 0.5
        }
    }
    
    @classmethod
    def get(cls, action_type: str) -> dict:
        """
        동작 타입에 맞는 가중치 프리셋 반환.
        
        Args:
            action_type: 동작 타입 (hurray, clapping, jumping 등)
            
        Returns:
            가중치 딕셔너리 {"upper_body_weight": ..., "lower_body_weight": ..., "head_weight": ...}
        """
        preset = cls.PRESETS.get(action_type.lower(), cls.PRESETS["default"])
        logger.debug(f"ActionWeightPresets: '{action_type}' -> {preset}")
        return preset
    
    @classmethod
    def list_actions(cls) -> list[str]:
        """사용 가능한 동작 타입 목록 반환."""
        return [k for k in cls.PRESETS.keys() if k != "default"]


@dataclass
class SimilarityResult:
    """
    유사도 계산 결과.
    
    Attributes:
        overall: 전체 유사도 (0~1)
        upper_body: 상체 유사도
        lower_body: 하체 유사도
        head: 머리 유사도
        frame_similarities: 프레임별 유사도 리스트
        valid_frame_ratio: 유효 프레임 비율
    """
    overall: float
    upper_body: float
    lower_body: float
    head: float
    frame_similarities: list[float] = field(default_factory=list)
    valid_frame_ratio: float = 1.0
    
    def to_dict(self) -> dict:
        """
        딕셔너리로 변환.
        
        Returns:
            결과 딕셔너리
        """
        return {
            "overall": round(self.overall, 4),
            "upper_body": round(self.upper_body, 4),
            "lower_body": round(self.lower_body, 4),
            "head": round(self.head, 4),
            "frame_similarities": [round(s, 4) for s in self.frame_similarities],
            "valid_frame_ratio": round(self.valid_frame_ratio, 4)
        }


class SimilarityCalculator:
    """
    동작 유사도 계산기.
    
    정렬된 두 시퀀스 간의 유사도를 계산합니다.
    
    Attributes:
        keypoint_groups: 부위별 키포인트 인덱스
        part_weights: 부위별 가중치
        
    Example:
        >>> calculator = SimilarityCalculator()
        >>> result = calculator.compute_similarity(aligned_query, aligned_ref)
        >>> print(f"Overall: {result.overall:.2%}")
    """
    
    def __init__(
        self,
        upper_body_weight: Optional[float] = None,
        lower_body_weight: Optional[float] = None,
        head_weight: Optional[float] = None,
        debug_mode: bool = False
    ):
        """
        SimilarityCalculator 초기화.
        
        Args:
            upper_body_weight: 상체 가중치 (None이면 설정값)
            lower_body_weight: 하체 가중치 (None이면 설정값)
            head_weight: 머리 가중치 (None이면 설정값)
            debug_mode: 디버그 모드 (상세 로깅 활성화)
        """
        # 부위별 키포인트 그룹
        self.keypoint_groups = {
            "upper_body": [
                KeypointIndex.L_SHOULDER, KeypointIndex.R_SHOULDER,
                KeypointIndex.L_ELBOW, KeypointIndex.R_ELBOW,
                KeypointIndex.L_WRIST, KeypointIndex.R_WRIST
            ],
            "lower_body": [
                KeypointIndex.L_HIP, KeypointIndex.R_HIP,
                KeypointIndex.L_KNEE, KeypointIndex.R_KNEE,
                KeypointIndex.L_ANKLE, KeypointIndex.R_ANKLE
            ],
            "head": [
                KeypointIndex.NOSE,
                KeypointIndex.L_EYE, KeypointIndex.R_EYE,
                KeypointIndex.L_EAR, KeypointIndex.R_EAR
            ]
        }
        
        # 부위별 가중치
        self.part_weights = {
            "upper_body": upper_body_weight or settings.SIMILARITY_UPPER_BODY_WEIGHT,
            "lower_body": lower_body_weight or settings.SIMILARITY_LOWER_BODY_WEIGHT,
            "head": head_weight or settings.SIMILARITY_HEAD_WEIGHT
        }
        
        self.min_keypoint_score = settings.MIN_KEYPOINT_SCORE
        self.debug_mode = debug_mode
        
        logger.info(f"SimilarityCalculator 초기화: weights={self.part_weights}, debug={debug_mode}")
    
    def compute_similarity(
        self,
        query: np.ndarray,
        reference: np.ndarray,
        aligned: bool = True,
        action_type: Optional[str] = None
    ) -> SimilarityResult:
        """
        두 시퀀스의 유사도 계산 (벡터화 버전).
        
        동작 타입에 따라 다른 유사도 계산 방식을 사용합니다:
        - 상체 동작(throwing, hurray, clapping): 코사인 유사도 (어깨, 팔 관절)
        - 하체 동작(kicking, jumping): 코사인 유사도 (골반, 다리 관절)
        - 전신 동작(walking_back): 코사인 유사도 (전체 관절)
        - 기타: 유클리드 거리 역수 (기존 방식)
        
        Args:
            query: 입력 시퀀스 shape (T, 17, 3)
            reference: 기준 시퀀스 shape (T, 17, 3)
            aligned: DTW 정렬 완료 여부
            action_type: 동작 타입 (throwing, hurray, clapping, kicking, jumping, walking_back 등)
            
        Returns:
            SimilarityResult 객체
            
        Raises:
            SimilarityError: 정렬되지 않은 시퀀스 또는 계산 오류
        """
        if not aligned:
            raise SimilarityError(
                "시퀀스가 정렬되지 않았습니다. DTWAligner를 먼저 사용하세요."
            )
        
        if len(query) != len(reference):
            raise SimilarityError(
                f"시퀀스 길이가 다릅니다: query={len(query)}, reference={len(reference)}"
            )
        
        if len(query) == 0:
            raise SimilarityError("시퀀스가 비어있습니다")
        
        T = len(query)
        
        # 동작 타입에 따른 유사도 계산 방식 결정
        use_cosine = self._should_use_cosine_similarity(action_type)
        if use_cosine:
            logger.info(f"코사인 유사도 사용 (동작: {action_type})")
        else:
            logger.info(f"유클리드 거리 역수 사용 (동작: {action_type})")
        
        # ====================================================================
        # 벡터화된 유사도 계산
        # ====================================================================
        
        # 1. 신뢰도 마스크 계산 (T, 17)
        q_scores = query[:, :, 2]
        r_scores = reference[:, :, 2]
        valid_keypoints = (q_scores > self.min_keypoint_score) & \
                          (r_scores > self.min_keypoint_score)
        
        # 2. 좌표 차이 및 거리 계산 (T, 17, 2) -> (T, 17)
        coords_diff = query[:, :, :2] - reference[:, :, :2]
        keypoint_distances = np.linalg.norm(coords_diff, axis=2)  # (T, 17)
        
        # 3. 무효한 키포인트는 NaN으로 마스킹
        keypoint_distances = np.where(valid_keypoints, keypoint_distances, np.nan)
        
        # 4. 부위별 유사도 계산
        part_similarities: dict[str, np.ndarray] = {}
        for part, indices in self.keypoint_groups.items():
            idx_list = [int(i) for i in indices]
            
            if use_cosine:
                # 코사인 유사도 계산
                part_similarities[part] = self._compute_part_cosine_similarity(
                    query, reference, idx_list, valid_keypoints
                )
            else:
                # 유클리드 거리 역수 계산 (기존 방식)
                part_distances = keypoint_distances[:, idx_list]  # (T, n_keypoints)
                
                # NaN 제외 평균 거리
                with np.errstate(all='ignore'):
                    mean_dist = np.nanmean(part_distances, axis=1)  # (T,)
                
                # 유클리드 거리 역수로 유사도 변환
                part_similarities[part] = self._euclidean_similarity(mean_dist)
        
        # 5. 가중 평균으로 프레임별 유사도 계산
        part_names = list(self.keypoint_groups.keys())
        weights = np.array([self.part_weights[p] for p in part_names])
        
        # (T, n_parts) 스택
        part_sims_stack = np.stack(
            [part_similarities[p] for p in part_names], axis=1
        )
        
        # NaN 처리된 가중 평균
        valid_parts_mask = ~np.isnan(part_sims_stack)  # (T, n_parts)
        weighted_sims = np.where(valid_parts_mask, part_sims_stack * weights, 0.0)
        weight_sums = np.sum(weights * valid_parts_mask, axis=1)  # (T,)
        
        # 안전한 나눗셈
        frame_similarities = np.divide(
            np.sum(weighted_sims, axis=1),
            weight_sums,
            out=np.full(T, DEFAULT_INVALID_SIMILARITY),
            where=weight_sums > EPSILON
        )
        
        # 6. 유효 프레임 비율 계산
        valid_keypoint_ratio = np.mean(valid_keypoints, axis=1)  # (T,)
        valid_frames = valid_keypoint_ratio > self.min_keypoint_score
        valid_frame_ratio = float(np.mean(valid_frames))
        
        # 7. 결과 집계
        # NaN을 0으로 대체하여 평균 계산
        frame_sims_clean = np.nan_to_num(frame_similarities, nan=0.0)
        upper_clean = np.nan_to_num(part_similarities["upper_body"], nan=0.0)
        lower_clean = np.nan_to_num(part_similarities["lower_body"], nan=0.0)
        head_clean = np.nan_to_num(part_similarities["head"], nan=0.0)
        
        # 8. 디버그 모드: 상세 로깅
        if self.debug_mode:
            self._log_debug_info(
                query, reference, 
                keypoint_distances, part_similarities,
                frame_sims_clean, valid_keypoints
            )
        
        result = SimilarityResult(
            overall=float(np.mean(frame_sims_clean)),
            upper_body=float(np.mean(upper_clean)),
            lower_body=float(np.mean(lower_clean)),
            head=float(np.mean(head_clean)),
            frame_similarities=frame_sims_clean.tolist(),
            valid_frame_ratio=valid_frame_ratio
        )
        
        logger.debug(
            f"유사도 계산 완료 (벡터화): overall={result.overall:.4f}, "
            f"valid_ratio={valid_frame_ratio:.2%}"
        )
        
        return result
    
    def _compute_part_similarity(
        self,
        q_frame: np.ndarray,
        r_frame: np.ndarray,
        indices: list[int]
    ) -> Optional[float]:
        """
        특정 부위의 유사도 계산.
        
        Args:
            q_frame: 쿼리 프레임 (17, 3)
            r_frame: 참조 프레임 (17, 3)
            indices: 부위 키포인트 인덱스
            
        Returns:
            유사도 (유효 키포인트 부족 시 None)
        """
        q_scores = q_frame[indices, 2]
        r_scores = r_frame[indices, 2]
        
        valid_mask = (q_scores > self.min_keypoint_score) & \
                     (r_scores > self.min_keypoint_score)
        
        if valid_mask.sum() < MIN_VALID_KEYPOINTS:
            return None
        
        valid_indices = np.array(indices)[valid_mask]
        
        q_points = q_frame[valid_indices, :2]  # (n, 2)
        r_points = r_frame[valid_indices, :2]  # (n, 2)
        
        # 유클리드 거리 계산
        distances = np.linalg.norm(q_points - r_points, axis=1)
        mean_distance = np.mean(distances)
        
        return float(self._euclidean_similarity(mean_distance))
    
    def _compute_weighted_frame_similarity(
        self,
        q_frame: np.ndarray,
        r_frame: np.ndarray
    ) -> float:
        """
        가중 프레임 유사도 계산 (레거시 - 유클리드 버전).
        
        Args:
            q_frame: 쿼리 프레임
            r_frame: 참조 프레임
            
        Returns:
            가중 평균 유사도
        """
        total_sim = 0.0
        total_weight = 0.0
        
        for part, indices in self.keypoint_groups.items():
            weight = self.part_weights[part]
            part_sim = self._compute_part_similarity_euclidean(q_frame, r_frame, indices)
            
            if part_sim is not None:
                total_sim += part_sim * weight
                total_weight += weight
        
        return total_sim / total_weight if total_weight > EPSILON else SIMILARITY_FLOOR
    
    def _compute_part_similarity_euclidean(
        self,
        q_frame: np.ndarray,
        r_frame: np.ndarray,
        indices: list[int]
    ) -> Optional[float]:
        """
        특정 부위의 유사도 계산 (유클리드 거리 역수).
        
        Args:
            q_frame: 쿼리 프레임 (17, 3)
            r_frame: 참조 프레임 (17, 3)
            indices: 부위 키포인트 인덱스
            
        Returns:
            유사도 (유효 키포인트 부족 시 None)
        """
        idx_list = [int(i) for i in indices]
        q_scores = q_frame[idx_list, 2]
        r_scores = r_frame[idx_list, 2]
        
        valid_mask = (q_scores > self.min_keypoint_score) & \
                     (r_scores > self.min_keypoint_score)
        
        if valid_mask.sum() < MIN_VALID_KEYPOINTS:
            return None
        
        valid_indices = np.array(idx_list)[valid_mask]
        
        q_points = q_frame[valid_indices, :2]  # (n, 2)
        r_points = r_frame[valid_indices, :2]  # (n, 2)
        
        # 유클리드 거리 계산
        distances = np.linalg.norm(q_points - r_points, axis=1)  # (n,)
        mean_distance = np.mean(distances)
        
        return float(self._euclidean_similarity(mean_distance))
    
    @staticmethod
    def _should_use_cosine_similarity(action_type: Optional[str]) -> bool:
        """
        동작 타입에 따라 코사인 유사도 사용 여부 결정.
        
        Args:
            action_type: 동작 타입
            
        Returns:
            코사인 유사도 사용 여부
        """
        if action_type is None:
            return False
        
        # 상체 동작: 공던지기, 만세, 박수
        upper_body_actions = ["throwing", "hurray", "clapping"]
        # 하체 동작: 공차기, 점프
        lower_body_actions = ["kicking", "jumping"]
        # 전신 동작: 뒤로 걷기
        full_body_actions = ["walking_back"]
        
        action_lower = action_type.lower()
        return action_lower in upper_body_actions + lower_body_actions + full_body_actions
    
    @staticmethod
    def _euclidean_similarity(distance: np.ndarray) -> np.ndarray:
        """
        유클리드 거리를 유사도로 변환.
        
        similarity = 1 / (1 + distance)
        
        좌표가 완벽히 일치하면 거리 0 → 유사도 1.0
        거리가 멀어질수록 유사도는 0에 수렴
        
        Args:
            distance: 거리 값 (스칼라 또는 배열)
            
        Returns:
            유사도 (0~1 범위)
        """
        return 1.0 / (1.0 + distance)
    
    def _compute_part_cosine_similarity(
        self,
        query: np.ndarray,
        reference: np.ndarray,
        indices: list[int],
        valid_keypoints: np.ndarray
    ) -> np.ndarray:
        """
        특정 부위의 코사인 유사도 계산.
        
        Args:
            query: 쿼리 시퀀스 (T, 17, 3)
            reference: 참조 시퀀스 (T, 17, 3)
            indices: 부위 키포인트 인덱스
            valid_keypoints: 유효 키포인트 마스크 (T, 17)
            
        Returns:
            프레임별 유사도 (T,)
        """
        T = len(query)
        part_sims = np.zeros(T)
        
        for t in range(T):
            # 해당 부위의 유효한 키포인트만 선택
            valid_mask = valid_keypoints[t, indices]
            if np.sum(valid_mask) < 2:
                part_sims[t] = 0.0
                continue
            
            # 유효한 키포인트의 좌표만 추출
            q_coords = query[t, indices, :2][valid_mask]  # (n, 2)
            r_coords = reference[t, indices, :2][valid_mask]  # (n, 2)
            
            # 벡터를 flatten
            q_flat = q_coords.flatten()  # (2n,)
            r_flat = r_coords.flatten()  # (2n,)
            
            # 코사인 유사도 계산
            dot_product = np.dot(q_flat, r_flat)
            q_norm = np.linalg.norm(q_flat)
            r_norm = np.linalg.norm(r_flat)
            
            if q_norm > EPSILON and r_norm > EPSILON:
                cos_sim = dot_product / (q_norm * r_norm)
                # -1~1 → 0~1 정규화
                part_sims[t] = (cos_sim + 1.0) / 2.0
            else:
                part_sims[t] = 0.0
        
        return part_sims
    
    @staticmethod
    def _cosine_similarity_vectorized(
        q_coords: np.ndarray,
        r_coords: np.ndarray
    ) -> np.ndarray:
        """
        코사인 유사도 계산 (벡터화, 비교용).
        
        cos_sim = (q · r) / (||q|| * ||r||)
        정규화: (cos_sim + 1) / 2 → 0~1 범위
        
        Args:
            q_coords: 쿼리 좌표 (T, 17, 2) 또는 (T, N)
            r_coords: 참조 좌표 (T, 17, 2) 또는 (T, N)
            
        Returns:
            프레임별 코사인 유사도 (T,)
        """
        # flatten to (T, D)
        if q_coords.ndim == 3:
            q_flat = q_coords.reshape(len(q_coords), -1)
            r_flat = r_coords.reshape(len(r_coords), -1)
        else:
            q_flat = q_coords
            r_flat = r_coords
        
        # 내적
        dot_product = np.sum(q_flat * r_flat, axis=1)  # (T,)
        
        # 노름
        q_norm = np.linalg.norm(q_flat, axis=1)  # (T,)
        r_norm = np.linalg.norm(r_flat, axis=1)  # (T,)
        
        # 안전한 나눗셈
        denom = q_norm * r_norm
        cos_sim = np.divide(
            dot_product, denom,
            out=np.zeros_like(dot_product),
            where=denom > EPSILON
        )
        
        # -1~1 → 0~1 정규화
        return (cos_sim + 1.0) / 2.0
    
    def _log_debug_info(
        self,
        query: np.ndarray,
        reference: np.ndarray,
        keypoint_distances: np.ndarray,
        part_similarities: dict[str, np.ndarray],
        frame_similarities: np.ndarray,
        valid_keypoints: np.ndarray
    ) -> None:
        """
        디버그 정보 상세 로깅.
        
        유클리드 방식과 코사인 방식을 비교하여 로깅합니다.
        """
        T = len(query)
        
        # 코사인 유사도 계산 (비교용)
        q_coords = query[:, :, :2]  # (T, 17, 2)
        r_coords = reference[:, :, :2]
        cosine_sims = self._cosine_similarity_vectorized(q_coords, r_coords)
        
        logger.info("=" * 70)
        logger.info("📊 유사도 계산 디버그 정보")
        logger.info("=" * 70)
        
        # 전체 통계
        logger.info(f"총 프레임 수: {T}")
        logger.info(f"유효 키포인트 비율 (평균): {np.mean(valid_keypoints):.2%}")
        
        # 거리 통계
        valid_distances = keypoint_distances[~np.isnan(keypoint_distances)]
        if len(valid_distances) > 0:
            logger.info(f"\n📏 키포인트 거리 통계:")
            logger.info(f"  - 최소: {np.min(valid_distances):.4f}")
            logger.info(f"  - 최대: {np.max(valid_distances):.4f}")
            logger.info(f"  - 평균: {np.mean(valid_distances):.4f}")
            logger.info(f"  - 표준편차: {np.std(valid_distances):.4f}")
        
        # 방식별 비교
        euclidean_mean = np.mean(frame_similarities)
        cosine_mean = np.mean(cosine_sims)
        
        logger.info(f"\n🔄 방식별 유사도 비교:")
        logger.info(f"  - 유클리드 역수 (현재): {euclidean_mean:.4f} ({euclidean_mean:.1%})")
        logger.info(f"  - 코사인 유사도 (참고): {cosine_mean:.4f} ({cosine_mean:.1%})")
        logger.info(f"  - 차이: {euclidean_mean - cosine_mean:+.4f}")
        
        # 부위별 유사도
        logger.info(f"\n🦴 부위별 유사도 (유클리드):")
        for part, sims in part_similarities.items():
            clean_sims = np.nan_to_num(sims, nan=0.0)
            logger.info(f"  - {part}: {np.mean(clean_sims):.4f}")
        
        # 샘플 프레임 상세 로깅
        sample_indices = np.linspace(0, T-1, min(DEBUG_LOG_SAMPLE_FRAMES, T), dtype=int)
        
        logger.info(f"\n📋 샘플 프레임 상세 ({len(sample_indices)}개):")
        logger.info("-" * 70)
        logger.info(f"{'Frame':>6} | {'Euclidean':>10} | {'Cosine':>10} | {'Diff':>10} | {'Avg Dist':>10}")
        logger.info("-" * 70)
        
        for idx in sample_indices:
            euc_sim = frame_similarities[idx]
            cos_sim = cosine_sims[idx]
            diff = euc_sim - cos_sim
            
            # 해당 프레임의 평균 거리
            frame_dist = keypoint_distances[idx]
            avg_dist = np.nanmean(frame_dist)
            
            logger.info(
                f"{idx:>6} | {euc_sim:>10.4f} | {cos_sim:>10.4f} | "
                f"{diff:>+10.4f} | {avg_dist:>10.4f}"
            )
        
        logger.info("-" * 70)
        logger.info("=" * 70)
    
    def compare_methods(
        self,
        query: np.ndarray,
        reference: np.ndarray
    ) -> dict:
        """
        유클리드와 코사인 방식을 비교하여 결과 반환.
        
        디버깅 및 방식 선택을 위한 비교 메서드입니다.
        
        Args:
            query: 입력 시퀀스 (T, 17, 3)
            reference: 참조 시퀀스 (T, 17, 3)
            
        Returns:
            비교 결과 딕셔너리
        """
        if len(query) != len(reference):
            raise SimilarityError("시퀀스 길이가 다릅니다")
        
        T = len(query)
        
        # 좌표 추출
        q_coords = query[:, :, :2]
        r_coords = reference[:, :, :2]
        
        # 유클리드 거리
        coords_diff = q_coords - r_coords
        keypoint_distances = np.linalg.norm(coords_diff, axis=2)  # (T, 17)
        mean_distances = np.mean(keypoint_distances, axis=1)  # (T,)
        
        # 유클리드 유사도
        euclidean_sims = self._euclidean_similarity(mean_distances)
        
        # 코사인 유사도
        cosine_sims = self._cosine_similarity_vectorized(q_coords, r_coords)
        
        return {
            "euclidean": {
                "frame_similarities": euclidean_sims.tolist(),
                "mean": float(np.mean(euclidean_sims)),
                "std": float(np.std(euclidean_sims)),
                "min": float(np.min(euclidean_sims)),
                "max": float(np.max(euclidean_sims))
            },
            "cosine": {
                "frame_similarities": cosine_sims.tolist(),
                "mean": float(np.mean(cosine_sims)),
                "std": float(np.std(cosine_sims)),
                "min": float(np.min(cosine_sims)),
                "max": float(np.max(cosine_sims))
            },
            "distance_stats": {
                "mean": float(np.mean(mean_distances)),
                "std": float(np.std(mean_distances)),
                "min": float(np.min(mean_distances)),
                "max": float(np.max(mean_distances))
            },
            "difference": {
                "mean_diff": float(np.mean(euclidean_sims) - np.mean(cosine_sims)),
                "correlation": float(np.corrcoef(euclidean_sims, cosine_sims)[0, 1])
            }
        }