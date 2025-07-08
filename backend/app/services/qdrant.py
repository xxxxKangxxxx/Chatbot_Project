"""
Qdrant 벡터 저장 및 검색 서비스 모듈

채팅 데이터의 벡터 저장, 검색, 필터링 기능을 제공합니다.
"""

from typing import List, Optional, Dict, Any, Union
import logging
from datetime import datetime, timedelta
from uuid import uuid4
from qdrant_client import QdrantClient
from qdrant_client.models import (
    VectorParams, Distance, PointStruct, Filter, FieldCondition, 
    MatchValue, Range, DatetimeRange, SearchParams, UpdateResult,
    CollectionInfo, ScoredPoint
)
from app.config import settings
from app.schemas.chat import ChatVectorPayload

logger = logging.getLogger(__name__)

class QdrantService:
    """Qdrant 벡터 데이터베이스 서비스"""
    
    def __init__(self):
        self.client = QdrantClient(
            url=settings.QDRANT_URL,
            api_key=settings.QDRANT_API_KEY if hasattr(settings, 'QDRANT_API_KEY') else None
        )
        self.collection_name = "chat_vectors"
        self.vector_dimension = 1536  # text-embedding-3-small 차원
        
    async def initialize_collection(self) -> bool:
        """
        컬렉션 초기화 (존재하지 않을 경우 생성)
        
        Returns:
            bool: 초기화 성공 여부
        """
        try:
            # 컬렉션 존재 확인
            collections = self.client.get_collections()
            collection_exists = any(
                collection.name == self.collection_name 
                for collection in collections.collections
            )
            
            if not collection_exists:
                # 컬렉션 생성
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=self.vector_dimension,
                        distance=Distance.COSINE
                    )
                )
                logger.info(f"Qdrant 컬렉션 생성 완료: {self.collection_name}")
            else:
                logger.info(f"Qdrant 컬렉션 이미 존재: {self.collection_name}")
            
            return True
            
        except Exception as e:
            logger.error(f"Qdrant 컬렉션 초기화 실패: {str(e)}")
            return False
    
    async def add_point(
        self,
        vector: List[float],
        payload: ChatVectorPayload,
        point_id: Optional[str] = None
    ) -> str:
        """
        벡터 포인트 추가
        
        Args:
            vector: 임베딩 벡터
            payload: 메타데이터
            point_id: 포인트 ID (없으면 자동 생성)
            
        Returns:
            str: 포인트 ID
        """
        try:
            if point_id is None:
                point_id = str(uuid4())
            
            # 페이로드를 딕셔너리로 변환
            payload_dict = payload.model_dump()
            
            # 날짜 형식 변환
            if payload_dict.get('timestamp'):
                payload_dict['timestamp'] = payload_dict['timestamp'].isoformat()
            
            point = PointStruct(
                id=point_id,
                vector=vector,
                payload=payload_dict
            )
            
            # 포인트 추가
            result = self.client.upsert(
                collection_name=self.collection_name,
                points=[point]
            )
            
            logger.info(f"벡터 포인트 추가 완료 - ID: {point_id}, 사용자: {payload.user_id}")
            
            return point_id
            
        except Exception as e:
            logger.error(f"벡터 포인트 추가 실패: {str(e)}")
            raise Exception(f"벡터 저장 중 오류 발생: {str(e)}")
    
    async def add_points_batch(
        self,
        vectors: List[List[float]],
        payloads: List[ChatVectorPayload],
        point_ids: Optional[List[str]] = None
    ) -> List[str]:
        """
        여러 벡터 포인트 일괄 추가
        
        Args:
            vectors: 임베딩 벡터 리스트
            payloads: 메타데이터 리스트
            point_ids: 포인트 ID 리스트 (없으면 자동 생성)
            
        Returns:
            List[str]: 포인트 ID 리스트
        """
        try:
            if len(vectors) != len(payloads):
                raise ValueError("벡터와 페이로드 수가 일치하지 않습니다")
            
            if point_ids is None:
                point_ids = [str(uuid4()) for _ in range(len(vectors))]
            elif len(point_ids) != len(vectors):
                raise ValueError("포인트 ID와 벡터 수가 일치하지 않습니다")
            
            points = []
            for i, (vector, payload) in enumerate(zip(vectors, payloads)):
                payload_dict = payload.model_dump()
                
                # 날짜 형식 변환
                if payload_dict.get('timestamp'):
                    payload_dict['timestamp'] = payload_dict['timestamp'].isoformat()
                
                points.append(PointStruct(
                    id=point_ids[i],
                    vector=vector,
                    payload=payload_dict
                ))
            
            # 배치 추가
            result = self.client.upsert(
                collection_name=self.collection_name,
                points=points
            )
            
            logger.info(f"배치 벡터 포인트 추가 완료 - 수량: {len(points)}")
            
            return point_ids
            
        except Exception as e:
            logger.error(f"배치 벡터 포인트 추가 실패: {str(e)}")
            raise Exception(f"배치 벡터 저장 중 오류 발생: {str(e)}")
    
    async def search_similar(
        self,
        query_vector: List[float],
        user_id: str,
        limit: int = 10,
        score_threshold: float = 0.7,
        filters: Optional[Dict[str, Any]] = None,
        exclude_roles: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        유사한 벡터 검색
        
        Args:
            query_vector: 검색할 벡터
            user_id: 사용자 ID
            limit: 반환할 최대 결과 수
            score_threshold: 최소 유사도 점수
            filters: 추가 필터 조건
            exclude_roles: 제외할 역할 리스트
            
        Returns:
            List[Dict[str, Any]]: 검색 결과
        """
        try:
            # 기본 필터 (사용자 ID)
            filter_conditions = [
                FieldCondition(
                    key="user_id",
                    match=MatchValue(value=user_id)
                )
            ]
            
            # 역할 제외 필터
            if exclude_roles:
                for role in exclude_roles:
                    filter_conditions.append(
                        FieldCondition(
                            key="role",
                            match=MatchValue(value=role)
                        )
                    )
            
            # 추가 필터 적용
            if filters:
                filter_conditions.extend(self._build_filter_conditions(filters))
            
            # 검색 실행
            search_result = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                query_filter=Filter(must=filter_conditions) if filter_conditions else None,
                limit=limit,
                score_threshold=score_threshold,
                with_payload=True
            )
            
            # 결과 변환
            results = []
            for point in search_result:
                result = {
                    "id": point.id,
                    "score": point.score,
                    "payload": point.payload
                }
                # 날짜 형식 복원
                if result["payload"].get("timestamp"):
                    result["payload"]["timestamp"] = datetime.fromisoformat(
                        result["payload"]["timestamp"]
                    )
                results.append(result)
            
            logger.info(f"유사 벡터 검색 완료 - 사용자: {user_id}, 결과: {len(results)}개")
            
            return results
            
        except Exception as e:
            logger.error(f"유사 벡터 검색 실패: {str(e)}")
            raise Exception(f"벡터 검색 중 오류 발생: {str(e)}")
    
    async def search_by_emotion(
        self,
        user_id: str,
        emotions: List[str],
        days_back: int = 30,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        감정별 대화 검색
        
        Args:
            user_id: 사용자 ID
            emotions: 검색할 감정 리스트
            days_back: 검색할 과거 일수
            limit: 반환할 최대 결과 수
            
        Returns:
            List[Dict[str, Any]]: 검색 결과
        """
        try:
            # 날짜 범위 설정
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days_back)
            
            # 필터 조건 구성
            filter_conditions = [
                FieldCondition(
                    key="user_id",
                    match=MatchValue(value=user_id)
                ),
                FieldCondition(
                    key="timestamp",
                    range=DatetimeRange(
                        gte=start_date,
                        lte=end_date
                    )
                )
            ]
            
            # 감정 필터 추가
            if emotions:
                emotion_conditions = [
                    FieldCondition(
                        key="emotion",
                        match=MatchValue(value=emotion)
                    ) for emotion in emotions
                ]
                filter_conditions.extend(emotion_conditions)
            
            # 검색 실행 (벡터 없이 필터만 사용)
            search_result = self.client.scroll(
                collection_name=self.collection_name,
                scroll_filter=Filter(must=filter_conditions),
                limit=limit,
                with_payload=True,
                with_vectors=False
            )
            
            # 결과 변환
            results = []
            for point in search_result[0]:  # scroll 결과의 첫 번째 요소
                result = {
                    "id": point.id,
                    "payload": point.payload
                }
                # 날짜 형식 복원
                if result["payload"].get("timestamp"):
                    result["payload"]["timestamp"] = datetime.fromisoformat(
                        result["payload"]["timestamp"]
                    )
                results.append(result)
            
            logger.info(f"감정별 검색 완료 - 사용자: {user_id}, 감정: {emotions}, 결과: {len(results)}개")
            
            return results
            
        except Exception as e:
            logger.error(f"감정별 검색 실패: {str(e)}")
            raise Exception(f"감정별 검색 중 오류 발생: {str(e)}")
    
    async def search_recent_context(
        self,
        user_id: str,
        hours_back: int = 24,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        최근 대화 컨텍스트 검색
        
        Args:
            user_id: 사용자 ID
            hours_back: 검색할 과거 시간
            limit: 반환할 최대 결과 수
            
        Returns:
            List[Dict[str, Any]]: 최근 대화 리스트
        """
        try:
            # 날짜 범위 설정
            end_date = datetime.now()
            start_date = end_date - timedelta(hours=hours_back)
            
            # 필터 조건 구성
            filter_conditions = [
                FieldCondition(
                    key="user_id",
                    match=MatchValue(value=user_id)
                ),
                FieldCondition(
                    key="timestamp",
                    range=DatetimeRange(
                        gte=start_date,
                        lte=end_date
                    )
                )
            ]
            
            # 검색 실행
            search_result = self.client.scroll(
                collection_name=self.collection_name,
                scroll_filter=Filter(must=filter_conditions),
                limit=limit,
                with_payload=True,
                with_vectors=False
            )
            
            # 결과 변환 및 시간순 정렬
            results = []
            for point in search_result[0]:
                result = {
                    "id": point.id,
                    "payload": point.payload
                }
                # 날짜 형식 복원
                if result["payload"].get("timestamp"):
                    result["payload"]["timestamp"] = datetime.fromisoformat(
                        result["payload"]["timestamp"]
                    )
                results.append(result)
            
            # 시간순 정렬 (최신순)
            results.sort(key=lambda x: x["payload"]["timestamp"], reverse=True)
            
            logger.info(f"최근 컨텍스트 검색 완료 - 사용자: {user_id}, 결과: {len(results)}개")
            
            return results
            
        except Exception as e:
            logger.error(f"최근 컨텍스트 검색 실패: {str(e)}")
            raise Exception(f"최근 컨텍스트 검색 중 오류 발생: {str(e)}")
    
    async def update_point(
        self,
        point_id: str,
        vector: Optional[List[float]] = None,
        payload: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        포인트 업데이트
        
        Args:
            point_id: 포인트 ID
            vector: 새로운 벡터 (선택사항)
            payload: 새로운 페이로드 (선택사항)
            
        Returns:
            bool: 업데이트 성공 여부
        """
        try:
            update_data = {}
            
            if vector is not None:
                update_data["vector"] = vector
            
            if payload is not None:
                # 날짜 형식 변환
                if payload.get('timestamp') and isinstance(payload['timestamp'], datetime):
                    payload['timestamp'] = payload['timestamp'].isoformat()
                update_data["payload"] = payload
            
            if not update_data:
                logger.warning(f"업데이트할 데이터가 없습니다 - 포인트 ID: {point_id}")
                return False
            
            # 포인트 업데이트
            result = self.client.upsert(
                collection_name=self.collection_name,
                points=[PointStruct(id=point_id, **update_data)]
            )
            
            logger.info(f"포인트 업데이트 완료 - ID: {point_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"포인트 업데이트 실패: {str(e)}")
            return False
    
    async def delete_point(self, point_id: str) -> bool:
        """
        포인트 삭제
        
        Args:
            point_id: 포인트 ID
            
        Returns:
            bool: 삭제 성공 여부
        """
        try:
            result = self.client.delete(
                collection_name=self.collection_name,
                points_selector=[point_id]
            )
            
            logger.info(f"포인트 삭제 완료 - ID: {point_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"포인트 삭제 실패: {str(e)}")
            return False
    
    async def delete_user_data(self, user_id: str) -> int:
        """
        사용자의 모든 벡터 데이터 삭제
        
        Args:
            user_id: 사용자 ID
            
        Returns:
            int: 삭제된 포인트 수
        """
        try:
            # 사용자 데이터 검색
            user_points = self.client.scroll(
                collection_name=self.collection_name,
                scroll_filter=Filter(
                    must=[
                        FieldCondition(
                            key="user_id",
                            match=MatchValue(value=user_id)
                        )
                    ]
                ),
                with_payload=False,
                with_vectors=False
            )
            
            point_ids = [point.id for point in user_points[0]]
            
            if point_ids:
                # 포인트 삭제
                result = self.client.delete(
                    collection_name=self.collection_name,
                    points_selector=point_ids
                )
                
                logger.info(f"사용자 데이터 삭제 완료 - 사용자: {user_id}, 삭제된 포인트: {len(point_ids)}개")
                
                return len(point_ids)
            else:
                logger.info(f"삭제할 사용자 데이터가 없습니다 - 사용자: {user_id}")
                return 0
                
        except Exception as e:
            logger.error(f"사용자 데이터 삭제 실패: {str(e)}")
            return 0
    
    def _build_filter_conditions(self, filters: Dict[str, Any]) -> List[FieldCondition]:
        """필터 조건 구성"""
        conditions = []
        
        for key, value in filters.items():
            if isinstance(value, list):
                # 리스트인 경우 OR 조건으로 처리
                for v in value:
                    conditions.append(
                        FieldCondition(key=key, match=MatchValue(value=v))
                    )
            elif isinstance(value, dict):
                # 범위 조건
                if 'gte' in value or 'lte' in value:
                    conditions.append(
                        FieldCondition(key=key, range=Range(**value))
                    )
            else:
                # 단일 값 매칭
                conditions.append(
                    FieldCondition(key=key, match=MatchValue(value=value))
                )
        
        return conditions
    
    async def get_collection_info(self) -> Dict[str, Any]:
        """
        컬렉션 정보 조회
        
        Returns:
            Dict[str, Any]: 컬렉션 정보
        """
        try:
            collection_info = self.client.get_collection(self.collection_name)
            
            return {
                "name": collection_info.config.params.vectors.size,
                "vectors_count": collection_info.vectors_count,
                "indexed_vectors_count": collection_info.indexed_vectors_count,
                "points_count": collection_info.points_count,
                "status": collection_info.status
            }
            
        except Exception as e:
            logger.error(f"컬렉션 정보 조회 실패: {str(e)}")
            return {"error": str(e)}
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Qdrant 서비스 상태 확인
        
        Returns:
            Dict[str, Any]: 상태 정보
        """
        try:
            # 컬렉션 존재 확인
            collections = self.client.get_collections()
            collection_exists = any(
                collection.name == self.collection_name 
                for collection in collections.collections
            )
            
            if not collection_exists:
                await self.initialize_collection()
            
            collection_info = await self.get_collection_info()
            
            return {
                "status": "healthy",
                "collection_name": self.collection_name,
                "collection_info": collection_info,
                "vector_dimension": self.vector_dimension
            }
            
        except Exception as e:
            logger.error(f"Qdrant 서비스 상태 확인 실패: {str(e)}")
            return {
                "status": "unhealthy",
                "error": str(e)
            }

# 전역 Qdrant 서비스 인스턴스
qdrant_service = QdrantService()

# 편의 함수들
async def add_vector(
    vector: List[float], 
    payload: ChatVectorPayload, 
    point_id: Optional[str] = None
) -> str:
    """벡터 추가"""
    return await qdrant_service.add_point(vector, payload, point_id)

async def search_similar_vectors(
    query_vector: List[float],
    user_id: str,
    limit: int = 10,
    score_threshold: float = 0.7
) -> List[Dict[str, Any]]:
    """유사 벡터 검색"""
    return await qdrant_service.search_similar(
        query_vector, user_id, limit, score_threshold
    )

async def get_recent_context(user_id: str, hours_back: int = 24) -> List[Dict[str, Any]]:
    """최근 대화 컨텍스트 조회"""
    return await qdrant_service.search_recent_context(user_id, hours_back) 