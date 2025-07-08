"""
서비스 계층 초기화 모듈

모든 비즈니스 서비스를 중앙에서 관리하고 제공합니다.
"""

from .gemini_embedding import (
    gemini_embedding_service as embedding_service,
    create_embedding,
    create_embeddings_batch,
    calculate_similarity
)

from .qdrant import (
    qdrant_service,
    add_vector,
    search_similar_vectors,
    get_recent_context
)

from .gpt import (
    gpt_service,
    generate_chat_response,
    generate_emotion_based_response
)

from .emotion import (
    emotion_service,
    analyze_text_emotion,
    get_emotion_trend,
    detect_emotion_patterns
)

from .user_profile import (
    user_profile_service,
    analyze_user_profile,
    get_personalized_recommendations
)

__all__ = [
    # 임베딩 서비스
    "embedding_service",
    "create_embedding",
    "create_embeddings_batch", 
    "calculate_similarity",
    
    # Qdrant 서비스
    "qdrant_service",
    "add_vector",
    "search_similar_vectors",
    "get_recent_context",
    
    # GPT 서비스
    "gpt_service",
    "generate_chat_response",
    "generate_emotion_based_response",
    
    # 감정 분석 서비스
    "emotion_service",
    "analyze_text_emotion",
    "get_emotion_trend",
    "detect_emotion_patterns",
    
    # 사용자 프로필 서비스
    "user_profile_service",
    "analyze_user_profile",
    "get_personalized_recommendations"
]

# 서비스 상태 확인 함수
async def check_all_services_health():
    """모든 서비스의 상태를 확인합니다."""
    health_status = {}
    
    try:
        # 임베딩 서비스 상태 확인
        health_status["embedding"] = await embedding_service.health_check()
    except Exception as e:
        health_status["embedding"] = {"status": "error", "error": str(e)}
    
    try:
        # Qdrant 서비스 상태 확인
        health_status["qdrant"] = await qdrant_service.health_check()
    except Exception as e:
        health_status["qdrant"] = {"status": "error", "error": str(e)}
    
    try:
        # GPT 서비스 상태 확인
        health_status["gpt"] = await gpt_service.health_check()
    except Exception as e:
        health_status["gpt"] = {"status": "error", "error": str(e)}
    
    try:
        # 감정 분석 서비스 상태 확인
        health_status["emotion"] = await emotion_service.health_check()
    except Exception as e:
        health_status["emotion"] = {"status": "error", "error": str(e)}
    
    try:
        # 사용자 프로필 서비스 상태 확인
        health_status["user_profile"] = await user_profile_service.health_check()
    except Exception as e:
        health_status["user_profile"] = {"status": "error", "error": str(e)}
    
    return health_status

# 서비스 초기화 함수
async def initialize_services():
    """모든 서비스를 초기화합니다."""
    try:
        # Qdrant 컬렉션 초기화
        await qdrant_service.initialize_collection()
        
        # 임베딩 차원 확인
        embedding_dim = await embedding_service.get_embedding_dimension()
        
        return {
            "status": "initialized",
            "embedding_dimension": embedding_dim,
            "services": ["embedding", "qdrant", "gpt", "emotion", "user_profile"]
        }
        
    except Exception as e:
        return {
            "status": "failed",
            "error": str(e)
        } 