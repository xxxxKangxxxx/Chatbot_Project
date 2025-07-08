"""
간단한 테스트용 FastAPI 애플리케이션
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# 간단한 FastAPI 앱 생성
app = FastAPI(
    title="고령층 개인화 챗봇 API - 테스트 버전",
    description="기본 동작 확인을 위한 간단한 버전",
    version="1.0.0-test"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """서비스 기본 정보"""
    return {
        "service": "고령층 개인화 챗봇 API",
        "version": "1.0.0-test",
        "status": "running",
        "message": "✅ FastAPI 서버가 정상적으로 실행 중입니다!"
    }

@app.get("/health")
async def health_check():
    """헬스 체크"""
    return {
        "status": "healthy",
        "message": "서버가 정상 작동 중입니다"
    }

@app.get("/test")
async def test_endpoint():
    """테스트 엔드포인트"""
    return {
        "message": "🎉 테스트 성공!",
        "features": [
            "FastAPI 정상 동작",
            "CORS 설정 완료",
            "기본 라우팅 작동"
        ]
    }

if __name__ == "__main__":
    import uvicorn
    print("🚀 테스트 서버 시작...")
    uvicorn.run(app, host="0.0.0.0", port=8000) 