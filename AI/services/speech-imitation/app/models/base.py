"""
모델 베이스 클래스

모든 AI 모델 래퍼의 공통 인터페이스를 정의합니다.

설계 원칙:
    - 싱글톤 패턴: 무거운 모델의 중복 로딩 방지
    - Lazy Loading: 필요 시점에 모델 로드
    - 추상화: 일관된 API 제공
"""

import logging
from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


class BaseModel(ABC, Generic[T]):
    """
    AI 모델 래퍼 베이스 클래스

    모든 모델 래퍼는 이 클래스를 상속하여 구현합니다.
    싱글톤 패턴과 Lazy Loading을 기본으로 지원합니다.

    Usage:
        class MyModel(BaseModel[MyModelType]):
            def _load_model(self) -> None:
                self._model = load_my_model()

            def predict(self, input_data) -> Any:
                self.ensure_loaded()
                return self._model.predict(input_data)
    """

    _instances: dict = {}  # 클래스별 싱글톤 인스턴스 저장
    _model: T | None = None
    _model_loaded: bool = False

    def __new__(cls) -> "BaseModel":
        """싱글톤 패턴 구현"""
        if cls not in cls._instances:
            instance = super().__new__(cls)
            instance._model = None
            instance._model_loaded = False
            cls._instances[cls] = instance
        return cls._instances[cls]

    @abstractmethod
    def _load_model(self) -> None:
        """
        모델 로드 (Lazy Loading)

        서브클래스에서 구현 필수.
        첫 predict 호출 시 자동으로 호출됩니다.

        구현 예시:
            def _load_model(self) -> None:
                self._model = SomeModel.load("model_path")
                logger.info("모델 로드 완료")
        """
        pass

    @abstractmethod
    def predict(self, *args: tuple, **kwargs: dict[str, Any]) -> Any:
        """
        추론 수행

        서브클래스에서 구현 필수.
        반드시 ensure_loaded()를 먼저 호출해야 합니다.

        구현 예시:
            def predict(self, input_data) -> Any:
                self.ensure_loaded()
                return self._model.predict(input_data)
        """
        pass

    def ensure_loaded(self) -> None:
        """모델이 로드되었는지 확인하고, 안되었으면 로드"""
        if not self._model_loaded:
            logger.info(f"{self.__class__.__name__} 모델 로딩 시작...")
            self._load_model()
            self._model_loaded = True
            logger.info(f"{self.__class__.__name__} 모델 로딩 완료")

    def unload(self) -> None:
        """모델 언로드 (메모리 해제)"""
        if self._model is not None:
            del self._model
            self._model = None
        self._model_loaded = False
        logger.info(f"{self.__class__.__name__} 모델 언로드")

    @property
    def is_loaded(self) -> bool:
        """모델 로드 상태 확인"""
        return self._model_loaded

    @classmethod
    def reset_instance(cls) -> None:
        """
        싱글톤 인스턴스 초기화 (테스트용)

        Warning: 프로덕션에서는 사용하지 마세요.
        """
        if cls in cls._instances:
            instance = cls._instances[cls]
            instance.unload()
            del cls._instances[cls]
        logger.debug(f"{cls.__name__} 인스턴스 초기화")

    @classmethod
    def reset_all_instances(cls) -> None:
        """
        모든 모델 인스턴스 초기화 (테스트/셧다운용)
        """
        for model_cls in list(cls._instances.keys()):
            model_cls.reset_instance()
        logger.info("모든 모델 인스턴스 초기화 완료")
