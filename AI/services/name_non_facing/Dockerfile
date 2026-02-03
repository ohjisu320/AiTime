 FROM nvidia/cuda:12.1.0-runtime-ubuntu22.04

WORKDIR /app

# 시스템 패키지 설치
RUN apt-get update && apt-get install -y \
    python3.11 \
    python3-pip \
    python3.11-venv \
    libgl1-mesa-glx \
    libglib2.0-0 \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Python 기본 설정
RUN ln -sf /usr/bin/python3.11 /usr/bin/python

# 의존성 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 앱 복사
COPY app/ ./app/

# YOLO 모델 복사
COPY *.pt ./

# 환경 변수
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# ============================================================
# 실행 모드 설정
# - 기본값: worker (RabbitMQ Consumer)
# - API 모드: docker run -e RUN_MODE=api ...
# ============================================================
ENV RUN_MODE=worker

# RabbitMQ 환경 변수 (docker-compose에서 오버라이드 가능)
ENV RABBITMQ_HOST=rabbitmq
ENV RABBITMQ_PORT=5672
ENV RABBITMQ_USER=guest
ENV RABBITMQ_PASSWORD=guest
ENV INPUT_QUEUE=analysis.name_non_facing.request
ENV OUTPUT_QUEUE=analysis.name_non_facing.result

# 포트 노출 (API 모드용)
EXPOSE 8000

# ============================================================
# 기본: Worker 실행 (RabbitMQ Consumer)
# API 모드: RUN_MODE=api 설정 시 uvicorn 실행
# ============================================================
CMD ["sh", "-c", "if [ \"$RUN_MODE\" = 'api' ]; then uvicorn app.main:app --host 0.0.0.0 --port 8000; else python -m app.worker; fi"]