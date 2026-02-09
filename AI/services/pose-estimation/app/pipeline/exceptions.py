# app/pipeline/exceptions.py
"""
파이프라인 커스텀 예외 모듈.

모든 파이프라인 관련 예외는 PipelineError를 상속합니다.
각 예외는 고유한 에러 코드와 상세 메시지를 포함합니다.
"""

from typing import Any, Optional


class PipelineError(Exception):
    """
    파이프라인 기본 예외.
    
    모든 파이프라인 관련 예외의 부모 클래스입니다.
    
    Attributes:
        code: 에러 코드 (API 응답용)
        message: 사용자 친화적 메시지
        details: 디버깅용 상세 정보
    """
    
    def __init__(
        self, 
        message: str, 
        code: str = "PIPELINE_ERROR",
        details: Optional[dict[str, Any]] = None
    ):
        """
        예외 초기화.
        
        Args:
            message: 에러 메시지
            code: 에러 코드
            details: 추가 상세 정보
        """
        self.code = code
        self.message = message
        self.details = details or {}
        super().__init__(self.message)
    
    def to_dict(self) -> dict[str, Any]:
        """
        예외를 딕셔너리로 변환.
        
        Returns:
            API 응답용 딕셔너리
        """
        return {
            "error_code": self.code,
            "message": self.message,
            "details": self.details
        }


class VideoProcessingError(PipelineError):
    """
    영상 처리 관련 예외.
    
    Examples:
        - 파일을 찾을 수 없음
        - 지원하지 않는 포맷
        - 손상된 영상 파일
    """
    
    def __init__(self, message: str, details: Optional[dict] = None):
        super().__init__(
            message=message,
            code="VIDEO_PROCESSING_ERROR",
            details=details
        )


class PoseExtractionError(PipelineError):
    """
    자세 추정 관련 예외.
    
    Examples:
        - 사람을 감지할 수 없음
        - 모델 추론 실패
        - 유효한 키포인트 부족
    """
    
    def __init__(self, message: str, details: Optional[dict] = None):
        super().__init__(
            message=message,
            code="POSE_EXTRACTION_ERROR",
            details=details
        )


class NormalizationError(PipelineError):
    """
    정규화 관련 예외.
    
    Examples:
        - 기준점(어깨, 골반) 감지 실패
        - 시퀀스가 비어있음
    """
    
    def __init__(self, message: str, details: Optional[dict] = None):
        super().__init__(
            message=message,
            code="NORMALIZATION_ERROR",
            details=details
        )


class DTWError(PipelineError):
    """
    DTW 정렬 관련 예외.
    
    Examples:
        - 시퀀스 길이가 0
        - 정렬 실패
    """
    
    def __init__(self, message: str, details: Optional[dict] = None):
        super().__init__(
            message=message,
            code="DTW_ERROR",
            details=details
        )


class SimilarityError(PipelineError):
    """
    유사도 계산 관련 예외.
    
    Examples:
        - 정렬되지 않은 시퀀스 입력
        - 계산 중 오류
    """
    
    def __init__(self, message: str, details: Optional[dict] = None):
        super().__init__(
            message=message,
            code="SIMILARITY_ERROR",
            details=details
        )


class ReferenceNotFoundError(PipelineError):
    """
    기준 동작 데이터를 찾을 수 없음.
    
    Examples:
        - 등록되지 않은 동작 유형
        - 기준 파일 누락
    """
    
    def __init__(self, action_type: str):
        super().__init__(
            message=f"Reference data not found for action: {action_type}",
            code="REFERENCE_NOT_FOUND",
            details={"action_type": action_type}
        )


class InvalidInputError(PipelineError):
    """
    잘못된 입력 데이터.
    
    Examples:
        - 월령 범위 초과
        - 잘못된 동작 유형
    """
    
    def __init__(self, message: str, field: str, value: Any):
        super().__init__(
            message=message,
            code="INVALID_INPUT",
            details={"field": field, "value": str(value)}
        )