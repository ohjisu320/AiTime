# Pose Worker

ViTPose 기반 인체 자세 추정 서비스

## 실행 방법

### 1. 환경 설정
\`\`\`bash
conda create -n pose-worker python=3.11 -y
conda activate pose-worker
pip install -r requirements.txt
\`\`\`

### 2. FastAPI 서버 실행
\`\`\`bash
python -m app.main
# 또는
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
\`\`\`

### 3. RabbitMQ Worker 실행
\`\`\`bash
python -m app.worker
\`\`\`

### 4. Docker 실행
\`\`\`bash
docker build -t pose-worker .
docker run --gpus all -p 8000:8000 pose-worker
\`\`\`

## API 문서
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc