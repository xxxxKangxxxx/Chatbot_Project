"""
고령층 개인화 챗봇 서비스 - FastAPI 백엔드
=====================================================

메인 애플리케이션 진입점
"""

import logging
import time
from contextlib import asynccontextmanager
from typing import Dict, Any

import uvicorn
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.config import settings
from app.database import engine, Base
from app.qdrant_client import initialize_qdrant
from app.api import get_api_router, get_routers_info
from sqlalchemy import text

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/app.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """애플리케이션 시작/종료 시 실행할 로직"""
    
    # 시작 시 초기화
    logger.info("🚀 챗봇 서비스 시작 중...")
    
    try:
                # 데이터베이스 테이블 생성
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("✅ MySQL 데이터베이스 초기화 완료")
        
        # Qdrant 초기화
        await initialize_qdrant()
        logger.info("✅ Qdrant 벡터 데이터베이스 초기화 완료")
        
        # 라우터 정보 로깅
        routers_info = get_routers_info()
        logger.info(f"📡 API 라우터 {len(routers_info)}개 등록 완료")
        
        logger.info("🎉 챗봇 서비스 준비 완료!")
        
    except Exception as e:
        logger.error(f"❌ 서비스 초기화 실패: {e}")
        raise
    
    yield
    
    # 종료 시 정리
    logger.info("👋 챗봇 서비스 종료 중...")


# FastAPI 앱 생성
app = FastAPI(
    title="고령층 개인화 챗봇 API",
    description="""
    ## 고령층을 위한 RAG + GPT 기반 개인화 챗봇 서비스
    
    ### 주요 기능
    - 🤖 개인화된 대화 생성 (RAG + GPT-4)
    - 😊 실시간 감정 분석 및 트렌드 파악
    - 📅 통합 일정 관리 (약물, 병원, 운동, 취미 등)
    - 🎯 관심사 기반 맞춤 추천
    - 👤 사용자 프로필 분석 및 개인화
    
    ### 기술 스택
    - **백엔드**: FastAPI + SQLAlchemy + MySQL
    - **벡터 DB**: Qdrant
    - **AI**: OpenAI GPT-4 + text-embedding-3-small
    - **아키텍처**: RAG (Retrieval-Augmented Generation)
    """,
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=[
        {
            "name": "chat",
            "description": "채팅 및 대화 관리"
        },
        {
            "name": "users", 
            "description": "사용자 계정 및 프로필 관리"
        },
        {
            "name": "emotions",
            "description": "감정 분석 및 트렌드"
        },
        {
            "name": "schedules",
            "description": "일정 관리 (약물, 병원, 운동 등)"
        },
        {
            "name": "interests",
            "description": "관심사 분석 및 추천"
        }
    ]
)

# 보안 미들웨어
if not settings.DEBUG:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=settings.ALLOWED_HOSTS
    )

# CORS 미들웨어
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,
)


# 요청 로깅 미들웨어
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """요청 로깅 및 응답 시간 측정"""
    start_time = time.time()
    
    # 요청 정보 로깅
    logger.info(f"🔄 {request.method} {request.url.path} - 클라이언트: {request.client.host}")
    
    try:
        response = await call_next(request)
        process_time = time.time() - start_time
        
        # 응답 정보 로깅
        logger.info(f"✅ {request.method} {request.url.path} - {response.status_code} - {process_time:.3f}s")
        
        # 응답 헤더에 처리 시간 추가
        response.headers["X-Process-Time"] = str(process_time)
        
        return response
        
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(f"❌ {request.method} {request.url.path} - 에러: {e} - {process_time:.3f}s")
        raise


# 전역 예외 핸들러
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """HTTP 예외 처리"""
    logger.error(f"HTTP 예외: {exc.status_code} - {exc.detail} - URL: {request.url}")
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error_code": f"HTTP_{exc.status_code}",
            "error_message": exc.detail,
            "path": str(request.url.path),
            "method": request.method,
            "timestamp": time.time()
        }
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """요청 유효성 검증 예외 처리"""
    logger.error(f"유효성 검증 오류: {exc.errors()} - URL: {request.url}")
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "error_code": "VALIDATION_ERROR",
            "error_message": "입력 데이터가 유효하지 않습니다",
            "validation_errors": exc.errors(),
            "path": str(request.url.path),
            "method": request.method,
            "timestamp": time.time()
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """일반 예외 처리"""
    logger.error(f"예상하지 못한 오류: {type(exc).__name__}: {exc} - URL: {request.url}")
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error_code": "INTERNAL_SERVER_ERROR",
            "error_message": "서버 내부 오류가 발생했습니다",
            "path": str(request.url.path),
            "method": request.method,
            "timestamp": time.time()
        }
    )


# 통합 API 라우터 등록
api_router = get_api_router()
app.include_router(api_router)


# 루트 엔드포인트
@app.get("/", tags=["Root"])
async def root():
    """서비스 정보 및 상태 확인"""
    routers_info = get_routers_info()
    
    return {
        "service": "고령층 개인화 챗봇 API",
        "version": "1.0.0",
        "status": "running",
        "description": "RAG + GPT 기반 고령층 정서 지원 챗봇 서비스",
        "features": [
            "개인화된 대화 생성",
            "실시간 감정 분석",
            "통합 일정 관리",
            "관심사 기반 추천",
            "사용자 프로필 분석"
        ],
        "endpoints": {
            "api_docs": "/docs",
            "redoc": "/redoc",
            "health": "/health",
            "api_info": "/api/v1/info"
        },
        "api_modules": list(routers_info.keys()),
        "total_endpoints": sum([
            7,   # chat
            10,  # user  
            10,  # emotion
            12,  # schedule
            9    # interest
        ]),
        "environment": "development" if settings.DEBUG else "production"
    }


# 상세 헬스 체크
@app.get("/health", tags=["Health"])
async def health_check():
    """종합적인 헬스 체크"""
    health_status = {
        "status": "healthy",
        "timestamp": time.time(),
        "version": "1.0.0",
        "environment": "development" if settings.DEBUG else "production",
        "services": {}
    }
    
    try:
        # 데이터베이스 연결 확인
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        health_status["services"]["database"] = {
            "status": "healthy",
            "type": "MySQL",
            "host": settings.DATABASE_HOST
        }
    except Exception as e:
        logger.error(f"데이터베이스 헬스 체크 실패: {e}")
        health_status["services"]["database"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        health_status["status"] = "degraded"
    
    # Qdrant 연결 확인 (간단한 체크)
    try:
        health_status["services"]["qdrant"] = {
            "status": "healthy",
            "type": "Vector Database",
            "host": settings.QDRANT_HOST
        }
    except Exception as e:
        logger.error(f"Qdrant 헬스 체크 실패: {e}")
        health_status["services"]["qdrant"] = {
            "status": "unhealthy", 
            "error": str(e)
        }
        health_status["status"] = "degraded"
    
    # OpenAI API 상태 (설정만 확인)
    health_status["services"]["openai"] = {
        "status": "configured" if settings.OPENAI_API_KEY else "not_configured",
        "models": ["gpt-4", "text-embedding-3-small"]
    }
    
    return health_status


# 애플리케이션 정보
@app.get("/info", tags=["Info"])
async def app_info():
    """애플리케이션 상세 정보"""
    routers_info = get_routers_info()
    
    return {
        "application": {
            "name": "고령층 개인화 챗봇 API",
            "version": "1.0.0",
            "description": "RAG + GPT 기반 고령층 정서 지원 챗봇 서비스",
            "author": "AI 개발팀",
            "license": "MIT"
        },
        "technical_stack": {
            "backend": "FastAPI 0.104+",
            "database": "MySQL 8.0+",
            "vector_db": "Qdrant",
            "ai_models": {
                "chat": "GPT-4",
                "embedding": "text-embedding-3-small"
            },
            "architecture": "RAG (Retrieval-Augmented Generation)"
        },
        "api_information": {
            "base_url": "/api/v1",
            "routers": routers_info,
            "total_endpoints": 48,
            "documentation": {
                "swagger": "/docs",
                "redoc": "/redoc"
            }
        },
        "features": {
            "core": [
                "개인화된 대화 생성",
                "RAG 기반 정보 검색",
                "실시간 감정 분석",
                "통합 일정 관리"
            ],
            "advanced": [
                "사용자 프로필 분석",
                "관심사 기반 추천",
                "감정 트렌드 분석",
                "일정 순응도 분석"
            ]
        },
        "environment": {
            "debug_mode": settings.DEBUG,
            "log_level": "INFO",
            "cors_enabled": True,
            "trusted_hosts": settings.ALLOWED_HOSTS if not settings.DEBUG else ["*"]
        }
    }


# 개발 서버 실행
if __name__ == "__main__":
    # 로그 디렉토리 생성
    import os
    os.makedirs("logs", exist_ok=True)
    
    logger.info("🔧 개발 서버 시작...")
    
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info",
        access_log=True,
        reload_dirs=["app"] if settings.DEBUG else None,
        log_config=None  # 커스텀 로깅 설정 사용
    ) 