"""
고령층 개인화 챗봇 서비스 - Qdrant 벡터 데이터베이스 스키마
=====================================================

이 파일은 Qdrant 벡터 데이터베이스의 컬렉션 구조와 
임베딩 저장/검색 로직을 정의합니다.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
from pydantic import BaseModel
from qdrant_client import QdrantClient
from qdrant_client.models import (
    CollectionInfo,
    VectorParams,
    Distance,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue,
    Range,
    DatetimeRange,
    UpdateResult
)
import uuid
import json


# =====================================================
# 1. Qdrant 컬렉션 설정
# =====================================================

class QdrantConfig:
    """Qdrant 설정 클래스"""
    
    # 컬렉션 이름
    CHAT_VECTORS_COLLECTION = "chat_vectors"
    
    # 임베딩 차원 (OpenAI text-embedding-ada-002 기준)
    EMBEDDING_DIMENSION = 1536
    
    # 거리 측정 방식 (코사인 유사도)
    DISTANCE_METRIC = Distance.COSINE
    
    # 검색 결과 개수 제한
    DEFAULT_SEARCH_LIMIT = 10
    MAX_SEARCH_LIMIT = 50


# =====================================================
# 2. 벡터 데이터 모델 정의
# =====================================================

class ChatVectorPayload(BaseModel):
    """채팅 벡터의 메타데이터 구조"""
    
    # 기본 정보
    user_id: int
    mysql_chat_id: int  # MySQL chat_logs 테이블의 ID
    role: str  # "user" or "bot"
    message: str
    
    # 시간 정보
    created_at: datetime
    session_id: Optional[str] = None
    
    # 감정 정보
    emotion: Optional[str] = None
    emotion_score: Optional[float] = None
    
    # 메시지 유형
    message_type: str = "text"  # text, button, medication, mood
    
    # 대화 맥락
    conversation_turn: Optional[int] = None  # 대화 순서
    response_to: Optional[str] = None  # 응답 대상 메시지 ID
    
    # 사용자 상태 (저장 시점)
    user_age: Optional[int] = None
    user_speech_style: Optional[str] = None
    
    # 관심사 태그
    interest_tags: List[str] = []
    
    # 추가 메타데이터
    metadata: Dict[str, Any] = {}


class VectorSearchResult(BaseModel):
    """벡터 검색 결과 구조"""
    
    vector_id: str
    score: float
    payload: ChatVectorPayload
    distance: float


# =====================================================
# 3. Qdrant 클라이언트 클래스
# =====================================================

class ChatbotQdrantClient:
    """챗봇용 Qdrant 클라이언트"""
    
    def __init__(self, host: str = "localhost", port: int = 6333):
        """
        Qdrant 클라이언트 초기화
        
        Args:
            host: Qdrant 서버 호스트
            port: Qdrant 서버 포트
        """
        self.client = QdrantClient(host=host, port=port)
        self.collection_name = QdrantConfig.CHAT_VECTORS_COLLECTION
        
    async def initialize_collection(self) -> bool:
        """
        채팅 벡터 컬렉션 초기화
        
        Returns:
            bool: 성공 여부
        """
        try:
            # 컬렉션 존재 확인
            collections = self.client.get_collections()
            collection_names = [col.name for col in collections.collections]
            
            if self.collection_name not in collection_names:
                # 컬렉션 생성
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=QdrantConfig.EMBEDDING_DIMENSION,
                        distance=QdrantConfig.DISTANCE_METRIC
                    )
                )
                print(f"✅ Qdrant 컬렉션 '{self.collection_name}' 생성 완료")
            else:
                print(f"✅ Qdrant 컬렉션 '{self.collection_name}' 이미 존재")
                
            return True
            
        except Exception as e:
            print(f"❌ Qdrant 컬렉션 초기화 실패: {e}")
            return False
    
    async def add_chat_vector(
        self, 
        embedding: List[float], 
        payload: ChatVectorPayload
    ) -> str:
        """
        채팅 벡터 추가
        
        Args:
            embedding: 임베딩 벡터
            payload: 메타데이터
            
        Returns:
            str: 벡터 ID
        """
        try:
            vector_id = str(uuid.uuid4())
            
            point = PointStruct(
                id=vector_id,
                vector=embedding,
                payload=payload.dict()
            )
            
            self.client.upsert(
                collection_name=self.collection_name,
                points=[point]
            )
            
            print(f"✅ 벡터 추가 완료: {vector_id}")
            return vector_id
            
        except Exception as e:
            print(f"❌ 벡터 추가 실패: {e}")
            raise
    
    async def search_similar_conversations(
        self,
        query_embedding: List[float],
        user_id: int,
        limit: int = QdrantConfig.DEFAULT_SEARCH_LIMIT,
        score_threshold: float = 0.7,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[VectorSearchResult]:
        """
        유사한 대화 검색
        
        Args:
            query_embedding: 검색 쿼리 임베딩
            user_id: 사용자 ID
            limit: 검색 결과 개수
            score_threshold: 유사도 임계값
            filters: 추가 필터 조건
            
        Returns:
            List[VectorSearchResult]: 검색 결과
        """
        try:
            # 기본 필터: 해당 사용자의 대화만 검색
            filter_conditions = [
                FieldCondition(
                    key="user_id",
                    match=MatchValue(value=user_id)
                )
            ]
            
            # 추가 필터 적용
            if filters:
                if "emotion" in filters:
                    filter_conditions.append(
                        FieldCondition(
                            key="emotion",
                            match=MatchValue(value=filters["emotion"])
                        )
                    )
                
                if "message_type" in filters:
                    filter_conditions.append(
                        FieldCondition(
                            key="message_type",
                            match=MatchValue(value=filters["message_type"])
                        )
                    )
                
                if "date_range" in filters:
                    start_date, end_date = filters["date_range"]
                    filter_conditions.append(
                        FieldCondition(
                            key="created_at",
                            range=DatetimeRange(
                                gte=start_date,
                                lte=end_date
                            )
                        )
                    )
            
            # 벡터 검색 수행
            search_results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                query_filter=Filter(must=filter_conditions),
                limit=min(limit, QdrantConfig.MAX_SEARCH_LIMIT),
                score_threshold=score_threshold
            )
            
            # 결과 변환
            results = []
            for result in search_results:
                vector_result = VectorSearchResult(
                    vector_id=result.id,
                    score=result.score,
                    payload=ChatVectorPayload(**result.payload),
                    distance=1.0 - result.score  # 코사인 거리 계산
                )
                results.append(vector_result)
            
            print(f"✅ 유사 대화 검색 완료: {len(results)}개 결과")
            return results
            
        except Exception as e:
            print(f"❌ 벡터 검색 실패: {e}")
            return []
    
    async def get_user_conversation_history(
        self,
        user_id: int,
        days: int = 7,
        limit: int = 50
    ) -> List[VectorSearchResult]:
        """
        사용자의 최근 대화 이력 조회
        
        Args:
            user_id: 사용자 ID
            days: 조회 기간 (일)
            limit: 결과 개수
            
        Returns:
            List[VectorSearchResult]: 대화 이력
        """
        try:
            from datetime import datetime, timedelta
            
            start_date = datetime.now() - timedelta(days=days)
            
            filter_conditions = [
                FieldCondition(
                    key="user_id",
                    match=MatchValue(value=user_id)
                ),
                FieldCondition(
                    key="created_at",
                    range=DatetimeRange(gte=start_date)
                )
            ]
            
            # 스크롤 검색으로 모든 결과 가져오기
            scroll_result = self.client.scroll(
                collection_name=self.collection_name,
                scroll_filter=Filter(must=filter_conditions),
                limit=limit,
                order_by="created_at"
            )
            
            results = []
            for point in scroll_result[0]:  # points
                vector_result = VectorSearchResult(
                    vector_id=point.id,
                    score=1.0,  # 스크롤 검색이므로 점수 없음
                    payload=ChatVectorPayload(**point.payload),
                    distance=0.0
                )
                results.append(vector_result)
            
            print(f"✅ 사용자 대화 이력 조회 완료: {len(results)}개")
            return results
            
        except Exception as e:
            print(f"❌ 대화 이력 조회 실패: {e}")
            return []
    
    async def delete_user_vectors(self, user_id: int) -> bool:
        """
        특정 사용자의 모든 벡터 삭제
        
        Args:
            user_id: 사용자 ID
            
        Returns:
            bool: 성공 여부
        """
        try:
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=Filter(
                    must=[
                        FieldCondition(
                            key="user_id",
                            match=MatchValue(value=user_id)
                        )
                    ]
                )
            )
            
            print(f"✅ 사용자 {user_id}의 벡터 삭제 완료")
            return True
            
        except Exception as e:
            print(f"❌ 벡터 삭제 실패: {e}")
            return False
    
    async def get_collection_stats(self) -> Dict[str, Any]:
        """
        컬렉션 통계 정보 조회
        
        Returns:
            Dict[str, Any]: 통계 정보
        """
        try:
            collection_info = self.client.get_collection(self.collection_name)
            
            stats = {
                "total_vectors": collection_info.points_count,
                "indexed_vectors": collection_info.indexed_vectors_count,
                "collection_status": collection_info.status,
                "vector_size": collection_info.config.params.vectors.size,
                "distance_metric": collection_info.config.params.vectors.distance.name
            }
            
            return stats
            
        except Exception as e:
            print(f"❌ 통계 조회 실패: {e}")
            return {}


# =====================================================
# 4. 컬렉션 초기화 스크립트
# =====================================================

async def initialize_qdrant_collections():
    """
    Qdrant 컬렉션 초기화
    """
    print("🚀 Qdrant 컬렉션 초기화 시작...")
    
    client = ChatbotQdrantClient()
    
    # 컬렉션 생성
    success = await client.initialize_collection()
    
    if success:
        print("✅ Qdrant 초기화 완료!")
        
        # 통계 정보 출력
        stats = await client.get_collection_stats()
        print(f"📊 컬렉션 정보:")
        for key, value in stats.items():
            print(f"   {key}: {value}")
    else:
        print("❌ Qdrant 초기화 실패!")
    
    return success


# =====================================================
# 5. 사용 예시
# =====================================================

if __name__ == "__main__":
    import asyncio
    
    async def example_usage():
        """사용 예시"""
        
        # 클라이언트 초기화
        client = ChatbotQdrantClient()
        await client.initialize_collection()
        
        # 예시 데이터
        example_payload = ChatVectorPayload(
            user_id=1,
            mysql_chat_id=123,
            role="user",
            message="오늘 기분이 좀 우울해요",
            created_at=datetime.now(),
            session_id="session_001",
            emotion="우울",
            emotion_score=-0.6,
            message_type="text",
            conversation_turn=1,
            user_age=65,
            user_speech_style="친근하고 따뜻한 말투",
            interest_tags=["감정", "일상"]
        )
        
        # 임베딩 벡터 (실제로는 OpenAI API에서 생성)
        example_embedding = [0.1] * QdrantConfig.EMBEDDING_DIMENSION
        
        # 벡터 추가
        vector_id = await client.add_chat_vector(
            embedding=example_embedding,
            payload=example_payload
        )
        
        print(f"추가된 벡터 ID: {vector_id}")
        
        # 유사 대화 검색
        search_results = await client.search_similar_conversations(
            query_embedding=example_embedding,
            user_id=1,
            limit=5
        )
        
        print(f"검색 결과: {len(search_results)}개")
        for result in search_results:
            print(f"  - {result.payload.message} (점수: {result.score})")
    
    # 실행
    asyncio.run(example_usage()) 