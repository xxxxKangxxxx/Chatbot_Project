"""
Qdrant 벡터 데이터베이스 클라이언트
=====================================================

Qdrant 벡터 데이터베이스와의 연결 및 초기화를 담당합니다.
"""

import logging
from typing import Optional
from qdrant_client import QdrantClient
from qdrant_client.http import models
from app.config import settings

logger = logging.getLogger(__name__)

# 전역 Qdrant 클라이언트 인스턴스
qdrant_client: Optional[QdrantClient] = None


def get_qdrant_client() -> QdrantClient:
    """Qdrant 클라이언트 인스턴스 반환"""
    global qdrant_client
    
    if qdrant_client is None:
        qdrant_client = QdrantClient(
            host=settings.QDRANT_HOST,
            port=settings.QDRANT_PORT,
            prefer_grpc=False  # HTTP 사용
        )
        logger.info(f"✅ Qdrant 클라이언트 연결: {settings.QDRANT_HOST}:{settings.QDRANT_PORT}")
    
    return qdrant_client


async def initialize_qdrant():
    """Qdrant 초기화 및 컬렉션 생성"""
    try:
        client = get_qdrant_client()
        
        # 컬렉션 존재 여부 확인
        collections = client.get_collections().collections
        collection_names = [col.name for col in collections]
        
        if settings.QDRANT_COLLECTION not in collection_names:
            # 컬렉션 생성
            client.create_collection(
                collection_name=settings.QDRANT_COLLECTION,
                vectors_config=models.VectorParams(
                    size=settings.EMBEDDING_DIMENSION,  # OpenAI embedding 차원
                    distance=models.Distance.COSINE,
                ),
            )
            logger.info(f"✅ Qdrant 컬렉션 생성: {settings.QDRANT_COLLECTION}")
        else:
            logger.info(f"✅ Qdrant 컬렉션 확인: {settings.QDRANT_COLLECTION}")
            
    except Exception as e:
        logger.warning(f"⚠️ Qdrant 초기화 실패 (테스트 환경에서는 정상): {e}")
        # 개발/테스트 환경에서는 Qdrant가 없어도 애플리케이션이 시작되도록 함


async def close_qdrant():
    """Qdrant 연결 종료"""
    global qdrant_client
    if qdrant_client:
        # Qdrant 클라이언트는 자동으로 연결을 관리하므로 특별한 close 메서드는 없음
        logger.info("🔌 Qdrant 클라이언트 연결 종료")
        qdrant_client = None 