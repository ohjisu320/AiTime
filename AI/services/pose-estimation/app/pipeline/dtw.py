# Ai/services/pose-estimation/app/pipeline/dtw.py
"""
Dynamic Time Warping 시간 정렬 모듈.

길이가 다른 두 시퀀스를 정렬하여 프레임 단위 비교가 가능하게 합니다.
Sakoe-Chiba 윈도우 제약을 적용하여 계산 효율성을 높입니다.

dtw-python 라이브러리를 사용하여 C 기반 가속으로 고성능 DTW 계산을 수행합니다.
"""

import numpy as np
import logging
from typing import Literal, Optional
from dtw import dtw as dtw_func

from app.config import settings
from app.pipeline.exceptions import DTWError

logger = logging.getLogger(__name__)

DistanceMetric = Literal["euclidean", "cosine", "manhattan"]


class DTWAligner:
    """
    DTW 기반 시퀀스 정렬기.
    
    두 시퀀스를 시간축에서 정렬하여 동일 길이로 만듭니다.
    dtw-python 라이브러리를 사용하여 고성능 DTW 계산을 수행합니다.
    
    Attributes:
        distance_metric: 거리 계산 방식
        window_ratio: Sakoe-Chiba 윈도우 비율
        
    Example:
        >>> aligner = DTWAligner()
        >>> aligned_q, aligned_r = aligner.align_sequences(query, reference)
        >>> assert len(aligned_q) == len(aligned_r)
    """
    
    def __init__(
        self,
        distance_metric: Optional[DistanceMetric] = None,
        window_ratio: Optional[float] = None
    ):
        """
        DTWAligner 초기화.
        
        Args:
            distance_metric: 거리 함수 (None이면 설정값 사용)
            window_ratio: Sakoe-Chiba 윈도우 비율 (0이면 제약 없음)
        """
        self.distance_metric = distance_metric or settings.DTW_DISTANCE_METRIC
        self.window_ratio = window_ratio if window_ratio is not None else settings.DTW_WINDOW_RATIO
        
        logger.info(
            f"DTWAligner 초기화: metric={self.distance_metric}, "
            f"window_ratio={self.window_ratio}"
        )
    
    def align_sequences(
        self,
        query: np.ndarray,
        reference: np.ndarray
    ) -> tuple[np.ndarray, np.ndarray]:
        """
        두 시퀀스를 DTW로 정렬.
        
        Args:
            query: 입력 시퀀스 shape (T1, 17, 3)
            reference: 기준 시퀀스 shape (T2, 17, 3)
            
        Returns:
            (aligned_query, aligned_reference) - 동일 길이
            
        Raises:
            DTWError: 정렬 실패
        """
        self._validate_sequences(query, reference)
        
        # 2D로 평탄화 (T, 17*3) -> (T, 51)
        query_flat = self._flatten_sequence(query)
        ref_flat = self._flatten_sequence(reference)
        
        # DTW 계산
        distance, path = self.compute_dtw(query_flat, ref_flat)
        
        logger.debug(f"DTW 거리: {distance:.4f}, 정렬 경로 길이: {len(path)}")
        
        # 정렬된 시퀀스 생성
        aligned_query = np.array([query[i] for i, j in path])
        aligned_ref = np.array([reference[j] for i, j in path])
        
        return aligned_query, aligned_ref
    
    def compute_dtw(
        self,
        seq1: np.ndarray,
        seq2: np.ndarray
    ) -> tuple[float, list[tuple[int, int]]]:
        """
        DTW 거리 및 정렬 경로 계산.
        
        dtw-python 라이브러리를 사용하여 고성능 DTW 계산을 수행합니다.
        
        Args:
            seq1: 시퀀스 1 shape (T1, D)
            seq2: 시퀀스 2 shape (T2, D)
            
        Returns:
            (dtw_distance, alignment_path)
        """
        T1, T2 = len(seq1), len(seq2)
        window_size = self._compute_window(T1, T2)
        
        # dtw-python 호출
        result = dtw_func(
            seq1, seq2,
            dist_method=self.distance_metric,
            window_type="sakoechiba" if window_size else None,
            window_args={"window_size": window_size} if window_size else {},
            keep_internals=True
        )
        
        # 경로 변환: index1, index2 -> list of tuples
        path = list(zip(result.index1.tolist(), result.index2.tolist()))
        
        return float(result.distance), path
    
    def compute_distance_only(
        self,
        seq1: np.ndarray,
        seq2: np.ndarray
    ) -> float:
        """
        DTW 거리만 계산 (경로 불필요시).
        
        Args:
            seq1: 시퀀스 1
            seq2: 시퀀스 2
            
        Returns:
            DTW 거리
        """
        distance, _ = self.compute_dtw(seq1, seq2)
        return distance
    
    def _validate_sequences(
        self,
        query: np.ndarray,
        reference: np.ndarray
    ) -> None:
        """
        시퀀스 유효성 검사.
        
        Args:
            query: 쿼리 시퀀스
            reference: 참조 시퀀스
            
        Raises:
            DTWError: 유효하지 않은 시퀀스
        """
        if query is None or len(query) == 0:
            raise DTWError("쿼리 시퀀스가 비어있습니다")
        
        if reference is None or len(reference) == 0:
            raise DTWError("참조 시퀀스가 비어있습니다")
        
        if query.shape[1:] != reference.shape[1:]:
            raise DTWError(
                f"시퀀스 형태가 일치하지 않습니다: "
                f"query={query.shape}, reference={reference.shape}"
            )
    
    def _flatten_sequence(self, sequence: np.ndarray) -> np.ndarray:
        """
        3D 시퀀스를 2D로 평탄화.
        
        Args:
            sequence: shape (T, 17, 3)
            
        Returns:
            shape (T, 51)
        """
        return sequence.reshape(len(sequence), -1)
    
    def _compute_window(self, T1: int, T2: int) -> Optional[int]:
        """
        Sakoe-Chiba 윈도우 크기 계산.
        
        Args:
            T1: 시퀀스 1 길이
            T2: 시퀀스 2 길이
            
        Returns:
            윈도우 크기 (0이면 None 반환)
        """
        if self.window_ratio <= 0:
            return None
        
        return max(1, int(max(T1, T2) * self.window_ratio))