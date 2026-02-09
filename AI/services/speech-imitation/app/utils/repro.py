"""
재현성(Reproductibility) 유틸리티

실행 당시의 코드(Git Commit)와 설정(Config) 상태를 기록하여,
나중에 동일한 환경에서 재실행하거나 원인 추적 가능
"""

import hashlib
import json
import logging
import subprocess
from typing import Any

logger = logging.getLogger(__name__)


def get_git_revision_hash() -> str:
    """
    현재 Git Commit Hash(Short) 반환
    Git이 없거나 실패하면 'unknown' 반환
    """
    try:
        # stderr를 DEVNULL로 보내서 에러 메시지 숨김
        return (
            subprocess.check_output(
                ["git", "rev-parse", "--short", "HEAD"], stderr=subprocess.DEVNULL
            )
            .decode("ascii")
            .strip()
        )
    except Exception:
        logger.debug("Git hash 추출 실패 (git 미설치 또는 .git 없음)")
        return "unknown"


def compute_config_hash(settings_obj: Any) -> str:
    """
    Config 객체(Pydantic Settings 등) 값 기반 해시 생성
    설정값 하나라도 바뀌면 해시 달라짐
    """
    try:
        # Pydantic v1/v2 호환 처리
        if hasattr(settings_obj, "model_dump"):
            d = settings_obj.model_dump()
        else:
            d = settings_obj.dict()

        # JSON 직렬화 (키 정렬 필수)
        s = json.dumps(d, sort_keys=True, default=str)

        # SHA256 해시 생성 (앞 16자리만 사용)
        return hashlib.sha256(s.encode("utf-8")).hexdigest()[:16]
    except Exception as e:
        logger.warning(f"Config hash 생성 실패: {e}")
        return "unknown"
