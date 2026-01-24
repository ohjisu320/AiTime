from fastapi import FastAPI

# 1. FastAPI 앱 인스턴스 생성
app = FastAPI()


# 2. 루트(/) 경로에 대한 GET 요청 처리
@app.get("/")
async def root():
    return {"message": "Hello World"}
