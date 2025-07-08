"""
임베딩 서비스 모듈

OpenAI text-embedding-3-small 모델을 사용하여
텍스트를 벡터로 변환하는 서비스를 제공합니다.
"""

from typing import List, Optional, Dict, Any
import asyncio
import logging
from openai import AsyncOpenAI
from app.config import settings

logger = logging.getLogger(__name__)

class EmbeddingService:
    """임베딩 생성 서비스"""
    
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = "text-embedding-3-small"
        self.max_batch_size = 100  # OpenAI API 배치 제한
        self.max_tokens = 8192     # 모델 토큰 제한
        
    async def create_embedding(
        self, 
        text: str, 
        user_id: Optional[str] = None
    ) -> List[float]:
        """
        단일 텍스트에 대한 임베딩 생성
        
        Args:
            text: 임베딩할 텍스트
            user_id: 사용자 ID (로깅용)
            
        Returns:
            List[float]: 임베딩 벡터
        """
        try:
            # 텍스트 전처리
            processed_text = self._preprocess_text(text)
            
            # OpenAI API 호출
            response = await self.client.embeddings.create(
                model=self.model,
                input=processed_text,
                encoding_format="float"
            )
            
            embedding = response.data[0].embedding
            
            logger.info(f"임베딩 생성 완료 - 사용자: {user_id}, 텍스트 길이: {len(text)}, 벡터 차원: {len(embedding)}")
            
            return embedding
            
        except Exception as e:
            logger.error(f"임베딩 생성 실패 - 사용자: {user_id}, 오류: {str(e)}")
            raise Exception(f"임베딩 생성 중 오류 발생: {str(e)}")
    
    async def create_embeddings_batch(
        self, 
        texts: List[str], 
        user_id: Optional[str] = None
    ) -> List[List[float]]:
        """
        여러 텍스트에 대한 임베딩 일괄 생성
        
        Args:
            texts: 임베딩할 텍스트 리스트
            user_id: 사용자 ID (로깅용)
            
        Returns:
            List[List[float]]: 임베딩 벡터 리스트
        """
        try:
            if not texts:
                return []
            
            # 배치 크기 제한 확인
            if len(texts) > self.max_batch_size:
                return await self._process_large_batch(texts, user_id)
            
            # 텍스트 전처리
            processed_texts = [self._preprocess_text(text) for text in texts]
            
            # OpenAI API 호출
            response = await self.client.embeddings.create(
                model=self.model,
                input=processed_texts,
                encoding_format="float"
            )
            
            embeddings = [data.embedding for data in response.data]
            
            logger.info(f"배치 임베딩 생성 완료 - 사용자: {user_id}, 텍스트 수: {len(texts)}")
            
            return embeddings
            
        except Exception as e:
            logger.error(f"배치 임베딩 생성 실패 - 사용자: {user_id}, 오류: {str(e)}")
            raise Exception(f"배치 임베딩 생성 중 오류 발생: {str(e)}")
    
    async def _process_large_batch(
        self, 
        texts: List[str], 
        user_id: Optional[str] = None
    ) -> List[List[float]]:
        """
        큰 배치를 작은 배치로 나누어 처리
        """
        all_embeddings = []
        
        for i in range(0, len(texts), self.max_batch_size):
            batch = texts[i:i + self.max_batch_size]
            batch_embeddings = await self.create_embeddings_batch(batch, user_id)
            all_embeddings.extend(batch_embeddings)
            
            # API 호출 제한 방지를 위한 대기
            if i + self.max_batch_size < len(texts):
                await asyncio.sleep(0.1)
        
        return all_embeddings
    
    def _preprocess_text(self, text: str) -> str:
        """
        텍스트 전처리
        
        Args:
            text: 원본 텍스트
            
        Returns:
            str: 전처리된 텍스트
        """
        if not text or not text.strip():
            return ""
        
        # 기본 정리
        processed = text.strip()
        
        # 연속된 공백 제거
        processed = " ".join(processed.split())
        
        # 토큰 길이 제한 (대략적인 계산)
        if len(processed) > self.max_tokens * 3:  # 한글 기준 대략적 계산
            processed = processed[:self.max_tokens * 3]
            logger.warning(f"텍스트가 너무 길어 잘림: {len(text)} -> {len(processed)}")
        
        return processed
    
    async def get_embedding_dimension(self) -> int:
        """
        임베딩 차원 수 반환
        
        Returns:
            int: 임베딩 벡터 차원
        """
        try:
            # 테스트 텍스트로 차원 확인
            test_embedding = await self.create_embedding("테스트")
            return len(test_embedding)
        except Exception as e:
            logger.error(f"임베딩 차원 확인 실패: {str(e)}")
            # text-embedding-3-small의 기본 차원
            return 1536
    
    async def calculate_similarity(
        self, 
        embedding1: List[float], 
        embedding2: List[float]
    ) -> float:
        """
        두 임베딩 간의 코사인 유사도 계산
        
        Args:
            embedding1: 첫 번째 임베딩 벡터
            embedding2: 두 번째 임베딩 벡터
            
        Returns:
            float: 코사인 유사도 (-1 ~ 1)
        """
        try:
            import numpy as np
            
            # 벡터 정규화
            norm1 = np.linalg.norm(embedding1)
            norm2 = np.linalg.norm(embedding2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            # 코사인 유사도 계산
            similarity = np.dot(embedding1, embedding2) / (norm1 * norm2)
            
            return float(similarity)
            
        except Exception as e:
            logger.error(f"유사도 계산 실패: {str(e)}")
            return 0.0
    
    async def health_check(self) -> Dict[str, Any]:
        """
        임베딩 서비스 상태 확인
        
        Returns:
            Dict[str, Any]: 상태 정보
        """
        try:
            # 간단한 테스트 임베딩 생성
            test_embedding = await self.create_embedding("건강 체크")
            
            return {
                "status": "healthy",
                "model": self.model,
                "embedding_dimension": len(test_embedding),
                "max_batch_size": self.max_batch_size,
                "max_tokens": self.max_tokens
            }
            
        except Exception as e:
            logger.error(f"임베딩 서비스 상태 확인 실패: {str(e)}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "model": self.model
            }

# 전역 임베딩 서비스 인스턴스
embedding_service = EmbeddingService()

# 편의 함수들
async def create_embedding(text: str, user_id: Optional[str] = None) -> List[float]:
    """텍스트에 대한 임베딩 생성"""
    return await embedding_service.create_embedding(text, user_id)

async def create_embeddings_batch(texts: List[str], user_id: Optional[str] = None) -> List[List[float]]:
    """여러 텍스트에 대한 임베딩 일괄 생성"""
    return await embedding_service.create_embeddings_batch(texts, user_id)

async def calculate_similarity(embedding1: List[float], embedding2: List[float]) -> float:
    """두 임베딩 간의 코사인 유사도 계산"""
    return await embedding_service.calculate_similarity(embedding1, embedding2) 