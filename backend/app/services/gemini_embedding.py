"""
Gemini 임베딩 서비스 모듈

Google Generative AI text-embedding-004 모델을 사용하여
텍스트를 벡터로 변환하는 서비스를 제공합니다.
"""

from typing import List, Optional, Dict, Any
import asyncio
import logging
import google.generativeai as genai
from app.config import settings

logger = logging.getLogger(__name__)

class GeminiEmbeddingService:
    """Gemini 임베딩 생성 서비스"""
    
    def __init__(self):
        # Gemini API 설정
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model_name = "text-embedding-004"
        self.max_batch_size = 100  # Gemini API 배치 제한
        self.max_tokens = 2048     # 모델 토큰 제한 (Gemini text-embedding-004)
        
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
            
            if not processed_text:
                logger.warning(f"빈 텍스트로 인한 기본 임베딩 반환 - 사용자: {user_id}")
                return [0.0] * 768  # text-embedding-004의 기본 차원
            
            # Gemini API 호출
            result = genai.embed_content(
                model=f"models/{self.model_name}",
                content=processed_text,
                task_type="semantic_similarity"
            )
            
            embedding = result['embedding']
            
            logger.info(f"Gemini 임베딩 생성 완료 - 사용자: {user_id}, 텍스트 길이: {len(text)}, 벡터 차원: {len(embedding)}")
            
            return embedding
            
        except Exception as e:
            logger.error(f"Gemini 임베딩 생성 실패 - 사용자: {user_id}, 오류: {str(e)}")
            # 오류 시 기본 임베딩 반환 (서비스 안정성을 위해)
            return [0.0] * 768
    
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
            
            # 빈 텍스트 필터링
            valid_texts = []
            valid_indices = []
            for i, text in enumerate(processed_texts):
                if text:
                    valid_texts.append(text)
                    valid_indices.append(i)
            
            if not valid_texts:
                logger.warning(f"모든 텍스트가 빈 값 - 사용자: {user_id}")
                return [[0.0] * 768 for _ in texts]
            
            # Gemini API는 현재 배치 임베딩을 직접 지원하지 않으므로 개별 처리
            embeddings_results = []
            for text in valid_texts:
                try:
                    result = genai.embed_content(
                        model=f"models/{self.model_name}",
                        content=text,
                        task_type="semantic_similarity"
                    )
                    embeddings_results.append(result['embedding'])
                    
                    # API 호출 제한 방지
                    await asyncio.sleep(0.1)
                    
                except Exception as e:
                    logger.error(f"개별 임베딩 생성 실패: {str(e)}")
                    embeddings_results.append([0.0] * 768)
            
            # 원본 순서에 맞게 결과 정렬
            final_embeddings = []
            valid_idx = 0
            for i in range(len(texts)):
                if i in valid_indices:
                    final_embeddings.append(embeddings_results[valid_idx])
                    valid_idx += 1
                else:
                    final_embeddings.append([0.0] * 768)
            
            logger.info(f"Gemini 배치 임베딩 생성 완료 - 사용자: {user_id}, 텍스트 수: {len(texts)}")
            
            return final_embeddings
            
        except Exception as e:
            logger.error(f"Gemini 배치 임베딩 생성 실패 - 사용자: {user_id}, 오류: {str(e)}")
            # 오류 시 기본 임베딩 리스트 반환
            return [[0.0] * 768 for _ in texts]
    
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
                await asyncio.sleep(0.5)  # Gemini는 좀 더 보수적으로
        
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
        
        # 토큰 길이 제한 (Gemini text-embedding-004 기준)
        if len(processed) > self.max_tokens * 2:  # 한글 기준 대략적 계산
            processed = processed[:self.max_tokens * 2]
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
            logger.error(f"Gemini 임베딩 차원 확인 실패: {str(e)}")
            # text-embedding-004의 기본 차원
            return 768
    
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
            
            # 벡터 길이 확인
            if len(embedding1) != len(embedding2):
                logger.error(f"임베딩 차원 불일치: {len(embedding1)} vs {len(embedding2)}")
                return 0.0
            
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
        Gemini 임베딩 API 상태 확인
        
        Returns:
            Dict[str, Any]: 상태 정보
        """
        try:
            # 간단한 테스트 임베딩 생성
            test_embedding = await self.create_embedding("건강 체크 테스트")
            
            if test_embedding and len(test_embedding) > 0:
                return {
                    "status": "healthy",
                    "model": self.model_name,
                    "api_accessible": True,
                    "embedding_dimension": len(test_embedding),
                    "test_embedding_norm": sum(x*x for x in test_embedding) ** 0.5
                }
            else:
                return {
                    "status": "unhealthy",
                    "model": self.model_name,
                    "api_accessible": False,
                    "error": "Empty embedding returned"
                }
                
        except Exception as e:
            return {
                "status": "unhealthy",
                "model": self.model_name,
                "api_accessible": False,
                "error": str(e)
            }


# 전역 서비스 인스턴스
gemini_embedding_service = GeminiEmbeddingService()


# 헬퍼 함수들 (기존 임베딩 서비스와 호환성을 위해)
async def create_embedding(text: str, user_id: Optional[str] = None) -> List[float]:
    """단일 임베딩 생성 (기존 서비스 호환)"""
    return await gemini_embedding_service.create_embedding(text, user_id)


async def create_embeddings_batch(texts: List[str], user_id: Optional[str] = None) -> List[List[float]]:
    """배치 임베딩 생성 (기존 서비스 호환)"""
    return await gemini_embedding_service.create_embeddings_batch(texts, user_id)


async def calculate_similarity(embedding1: List[float], embedding2: List[float]) -> float:
    """유사도 계산 (기존 서비스 호환)"""
    return await gemini_embedding_service.calculate_similarity(embedding1, embedding2) 