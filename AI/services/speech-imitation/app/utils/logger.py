"""
로깅 유틸리티
- 서비스 단일 진입점에서 setup_logging()만 호출하면,
  모듈 전반에 일관된 로그 포맷을 적용합니다.
"""

from __future__ import annotations

import logging
import sys


def setup_logging(level: str = "INFO") -> None:
    level = (level or "INFO").upper()
    logging.basicConfig(
        level=getattr(logging, level, logging.INFO),
        stream=sys.stdout,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
