"""
API 라우터 통합 관리

모든 API 라우터를 중앙에서 관리하고 FastAPI 애플리케이션에 등록합니다.
"""

from fastapi import APIRouter
from .chat import router as chat_router
from .user import router as user_router
from .emotion import router as emotion_router
from .schedule import router as schedule_router
from .interest import router as interest_router

# 메인 API 라우터 생성
api_router = APIRouter(prefix="/api/v1")

# 각 라우터를 메인 라우터에 포함
api_router.include_router(chat_router)
api_router.include_router(user_router)
api_router.include_router(emotion_router)
api_router.include_router(schedule_router)
api_router.include_router(interest_router)

# 라우터 정보
ROUTERS_INFO = {
    "chat": {
        "prefix": "/chat",
        "tags": ["chat"],
        "description": "채팅 관련 API - 대화 처리, 세션 관리, 통계"
    },
    "user": {
        "prefix": "/users",
        "tags": ["users"],
        "description": "사용자 관련 API - 등록, 조회, 수정, 프로필 분석"
    },
    "emotion": {
        "prefix": "/emotions",
        "tags": ["emotions"],
        "description": "감정 관련 API - 분석, 트렌드, 패턴, 인사이트"
    },
    "schedule": {
        "prefix": "/schedules",
        "tags": ["schedules"],
        "description": "일정 관리 API - 약물, 병원, 운동, 취미, 개인 일정"
    },
    "interest": {
        "prefix": "/interests",
        "tags": ["interests"],
        "description": "관심사 관련 API - 분석, 추천, 트렌드, 컨텐츠"
    }
}

def get_api_router():
    """
    설정된 API 라우터 반환
    """
    return api_router

def get_routers_info():
    """
    등록된 라우터 정보 반환
    """
    return ROUTERS_INFO

# 헬스체크 엔드포인트
@api_router.get("/health")
async def health_check():
    """
    API 서버 상태 확인
    """
    return {
        "status": "healthy",
        "message": "고령층 챗봇 API 서버가 정상 작동 중입니다",
        "version": "1.0.0",
        "routers": list(ROUTERS_INFO.keys())
    }

# API 정보 엔드포인트
@api_router.get("/info")
async def api_info():
    """
    API 정보 조회
    """
    return {
        "api_name": "고령층 개인화 챗봇 API",
        "version": "1.0.0",
        "description": "RAG + GPT 기반 고령층 맞춤형 챗봇 서비스",
        "features": [
            "개인화된 대화 생성",
            "감정 분석 및 트렌드",
            "일정 관리 (약물, 병원, 운동 등)",
            "관심사 기반 추천",
            "사용자 프로필 분석"
        ],
        "routers": ROUTERS_INFO,
        "endpoints_count": {
            "chat": 7,
            "user": 10,
            "emotion": 10,
            "schedule": 12,
            "interest": 9
        },
        "total_endpoints": 48
    } 