# services/name_non_facing/app/pipeline/stages/base_stage.py
"""
파이프라인 Stage 베이스 클래스

파이프라인의 각 단계를 만들 때 반드시 지켜야할 규칙과, 공통적으로 해야 할 일을 정의해둔 부모 클래스!
- run (): 실제 작업을 시키기 전후에 공통적으로 해야 하는 일: "시작 시간 재기" → "로그 남기기(시작)" → "일 시키기(process)" → "에러 나면 기록하기" → "소요 시간 계산해서 기록하기" → "로그 남기기(완료)"
- process() : 각 Stage가 실제로 해야 하는 일을 구현하는 메서드. (자식 클래스에서 반드시 구현해야 함)

설계 의도:
다음과 같은 귀찮은 일들을 미리 해줘서, 상속 받기만 하면, 새로운 단계를 만들 때마다 시간 측정 코드나 에러 처리 코드를 반복 작성하지 않도록 합니다.
- 유효성 검사 (validate): 작업을 시작하기 전에 필요한 데이터(예: 비디오 파일 경로)가 있는지 미리 검사합니다.
- 시간 측정: 이 단계가 0.5초 걸렸는지, 3초 걸렸는지 자동으로 context에 기록됩니다.
- 에러 핸들링: 작업 도중 에러가 터지면, 프로그램이 멈추기 전에 context에 에러 내용을 기록하고 로그를 남겨 디버깅을 돕습니다.

Reference:
    - Template Method Pattern: https://refactoring.guru/design-patterns/template-method
    - Chain of Responsibility: https://refactoring.guru/design-patterns/chain-of-responsibility
"""

from abc import ABC, abstractmethod
from typing import Optional
import logging
import time

from app.pipeline.context import PipelineContext

logger = logging.getLogger(__name__)


class BaseStage(ABC):
    """
    파이프라인 Stage 베이스 클래스
    
    모든 Stage는 이 클래스를 상속하여 구현합니다.
    
    Template Method Pattern:
        - run(): 공통 로직 (타이밍, 로깅, 에러 처리)
        - process(): 각 Stage의 구체적 구현
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """
        Stage 이름
        
        로깅, 타이밍 기록 등에 사용됩니다.
        고유하고 명확한 이름을 반환해야 합니다.
        """
        pass
    
    @abstractmethod
    def process(self, context: PipelineContext) -> PipelineContext:
        """
        Stage 처리 수행 (서브클래스 구현 필수)
        
        Args:
            context: 파이프라인 컨텍스트
            
        Returns:
            업데이트된 컨텍스트
            
        Note:
            - context의 필요한 필드만 수정
            - 에러 발생 시 예외를 throw (run에서 처리)
        """
        pass
    
    def validate(self, context: PipelineContext) -> Optional[str]:
        """
        Stage 실행 전 검증 (선택적 오버라이드)
        
        Args:
            context: 파이프라인 컨텍스트
            
        Returns:
            에러 메시지 (None이면 검증 통과)
        """
        return None
    
    def run(self, context: PipelineContext) -> PipelineContext:
        """
        Stage 실행 (Template Method)
        
        공통 로직을 포함:
        1. 사전 검증
        2. 타이밍 시작
        3. process() 호출
        4. 타이밍 종료 및 기록
        5. 에러 처리
        
        Args:
            context: 파이프라인 컨텍스트
            
        Returns:
            업데이트된 컨텍스트
            
        Raises:
            Exception: process()에서 발생한 예외 (로깅 후 재발생)
        """
        # 사전 검증
        validation_error = self.validate(context)
        if validation_error:
            logger.error(f"✖️ {self.name} 검증 실패: {validation_error}")
            context.add_error(self.name, validation_error)
            raise ValueError(validation_error)
        
        logger.info(f"🩷🩷🩷 {self.name} 시작")
        start_time = time.time()
        
        try:
            context = self.process(context)
        except Exception as e:
            elapsed = time.time() - start_time
            context.record_time(self.name, elapsed)
            logger.error(f"✖️✖️✖️ {self.name} 실패 ({elapsed:.2f}s): {e}")
            context.add_error(self.name, str(e))
            raise
        
        elapsed = time.time() - start_time
        context.record_time(self.name, elapsed)
        logger.info(f"💚💚💚 {self.name} 완료 ({elapsed:.2f}s)")
        
        return context
    
    def __repr__(self) -> str:
        return f"<{self.name}>"
