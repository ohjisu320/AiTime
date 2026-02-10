FROM python:3.11-slim

WORKDIR /app

# 시스템 패키지 설치
# - ffmpeg: 오디오 처리 (librosa, torchaudio)
# - libsndfile1: soundfile 라이브러리
# - curl: 헬스체크 등
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsndfile1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 파이썬 기본 설정
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# 의존성 설치
# 1. PyTorch CPU 버전 먼저 설치 (이미지 크기 최적화)
RUN pip install --no-cache-dir torch torchaudio --index-url https://download.pytorch.org/whl/cpu

# 2. 나머지 의존성 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 앱 복사
COPY app/ ./app/

# ============================================================
# 실행 명령 (Worker 실행)
# ============================================================
CMD ["python", "-m", "app.worker"]
