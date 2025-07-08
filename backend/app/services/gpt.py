"""
GPT 프롬프트 구성 및 응답 생성 서비스 모듈

사용자 정보와 대화 컨텍스트를 기반으로 개인화된 GPT 응답을 생성합니다.
"""

from typing import List, Dict, Any, Optional, Tuple
import logging
from datetime import datetime
from openai import AsyncOpenAI
from app.config import settings
from app.models.user import User
from app.models.interest import Interest
from app.models.emotion import EmotionSummary
from app.schemas.chat import ChatPromptContext, ChatResponse

logger = logging.getLogger(__name__)

class GPTService:
    """GPT 응답 생성 서비스"""
    
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = "gpt-4o-mini"  # 또는 "gpt-3.5-turbo"
        self.max_tokens = 2000
        self.temperature = 0.7
        
    async def generate_response(
        self,
        user_message: str,
        user_info: Dict[str, Any],
        context: ChatPromptContext,
        conversation_history: List[Dict[str, Any]] = None
    ) -> ChatResponse:
        """
        사용자 메시지에 대한 GPT 응답 생성
        
        Args:
            user_message: 사용자 메시지
            user_info: 사용자 정보
            context: 대화 컨텍스트
            conversation_history: 최근 대화 기록
            
        Returns:
            ChatResponse: GPT 응답
        """
        try:
            # 시스템 프롬프트 구성
            system_prompt = self._build_system_prompt(user_info, context)
            
            # 대화 히스토리 구성
            messages = self._build_conversation_messages(
                system_prompt, user_message, conversation_history
            )
            
            # GPT API 호출
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                presence_penalty=0.1,
                frequency_penalty=0.1
            )
            
            # 응답 텍스트 추출
            response_text = response.choices[0].message.content
            
            # 응답 후처리
            processed_response = self._post_process_response(
                response_text, user_info
            )
            
            # 토큰 사용량 정보
            usage_info = {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            }
            
            logger.info(f"GPT 응답 생성 완료 - 사용자: {user_info.get('user_id')}, 토큰: {usage_info['total_tokens']}")
            
            return ChatResponse(
                message=processed_response,
                role="assistant",
                timestamp=datetime.now(),
                metadata={
                    "model": self.model,
                    "usage": usage_info,
                    "context_used": len(context.similar_conversations) > 0,
                    "emotion_context": context.recent_emotions
                }
            )
            
        except Exception as e:
            logger.error(f"GPT 응답 생성 실패: {str(e)}")
            # 기본 응답 반환
            return ChatResponse(
                message="죄송합니다. 지금은 응답을 생성할 수 없습니다. 잠시 후 다시 시도해주세요.",
                role="assistant",
                timestamp=datetime.now(),
                metadata={"error": str(e)}
            )
    
    def _build_system_prompt(
        self, 
        user_info: Dict[str, Any], 
        context: ChatPromptContext
    ) -> str:
        """
        시스템 프롬프트 구성
        
        Args:
            user_info: 사용자 정보
            context: 대화 컨텍스트
            
        Returns:
            str: 시스템 프롬프트
        """
        # 기본 역할 설정
        base_prompt = f"""당신은 고령층을 위한 따뜻하고 친근한 AI 동반자입니다.
사용자의 외로움을 달래고 정서적 지원을 제공하는 것이 주요 목표입니다.

사용자 정보:
- 이름: {user_info.get('name', '사용자')}님
- 나이: {user_info.get('age', '미상')}세
- 선호 말투: {user_info.get('preferred_tone', '정중한 말투')}
- 성격: {user_info.get('personality_traits', '친근함')}

대화 원칙:
1. 항상 존댓말을 사용하고 따뜻하게 대화하세요
2. 사용자의 감정에 공감하고 이해를 표현하세요
3. 긍정적이고 희망적인 메시지를 전달하세요
4. 복잡한 용어보다는 쉽고 친근한 표현을 사용하세요
5. 사용자의 관심사와 취미를 적극적으로 활용하세요"""
        
        # 관심사 정보 추가
        if context.user_interests:
            interests_text = ", ".join(context.user_interests)
            base_prompt += f"\n\n사용자의 관심사: {interests_text}"
            base_prompt += "\n대화 중에 이런 관심사들을 자연스럽게 언급해보세요."
        
        # 최근 감정 상태 반영
        if context.recent_emotions:
            emotions_text = ", ".join(context.recent_emotions)
            base_prompt += f"\n\n최근 감정 상태: {emotions_text}"
            base_prompt += "\n사용자의 감정 상태를 고려하여 적절한 위로나 격려를 해주세요."
        
        # 유사한 과거 대화 컨텍스트 활용
        if context.similar_conversations:
            base_prompt += "\n\n과거 비슷한 대화 내용:"
            for i, conv in enumerate(context.similar_conversations[:3]):  # 최대 3개만
                base_prompt += f"\n{i+1}. {conv.get('content', '')[:100]}..."
            base_prompt += "\n이전 대화 내용을 참고하여 연속성 있는 대화를 이어가세요."
        
        # 말투 적용
        tone_instructions = self._get_tone_instructions(user_info.get('preferred_tone'))
        if tone_instructions:
            base_prompt += f"\n\n말투 가이드: {tone_instructions}"
        
        return base_prompt
    
    def _get_tone_instructions(self, preferred_tone: str) -> str:
        """말투별 지침 반환"""
        tone_map = {
            "친근한": "친구처럼 편안하고 따뜻하게 대화하되, 존댓말은 유지하세요.",
            "정중한": "격식을 갖춘 정중한 말투로 대화하세요.",
            "유머러스한": "적절한 유머를 섞어 즐겁게 대화하세요.",
            "차분한": "차분하고 안정적인 톤으로 대화하세요.",
            "격려하는": "항상 긍정적이고 격려하는 말투로 대화하세요."
        }
        return tone_map.get(preferred_tone, "")
    
    def _build_conversation_messages(
        self,
        system_prompt: str,
        user_message: str,
        conversation_history: List[Dict[str, Any]] = None
    ) -> List[Dict[str, str]]:
        """
        대화 메시지 구성
        
        Args:
            system_prompt: 시스템 프롬프트
            user_message: 사용자 메시지
            conversation_history: 대화 기록
            
        Returns:
            List[Dict[str, str]]: 메시지 리스트
        """
        messages = [
            {"role": "system", "content": system_prompt}
        ]
        
        # 최근 대화 기록 추가 (최대 10개)
        if conversation_history:
            for msg in conversation_history[-10:]:
                messages.append({
                    "role": msg.get("role", "user"),
                    "content": msg.get("content", "")
                })
        
        # 현재 사용자 메시지 추가
        messages.append({
            "role": "user",
            "content": user_message
        })
        
        return messages
    
    def _post_process_response(
        self, 
        response_text: str, 
        user_info: Dict[str, Any]
    ) -> str:
        """
        응답 후처리
        
        Args:
            response_text: 원본 응답
            user_info: 사용자 정보
            
        Returns:
            str: 후처리된 응답
        """
        if not response_text:
            return "죄송합니다. 응답을 생성할 수 없습니다."
        
        # 기본 정리
        processed = response_text.strip()
        
        # 사용자 이름 개인화
        user_name = user_info.get('name', '사용자')
        if user_name != '사용자' and user_name not in processed:
            # 자연스럽게 이름 언급 (가끔씩)
            import random
            if random.random() < 0.3:  # 30% 확률
                processed = f"{user_name}님, " + processed
        
        # 길이 제한
        if len(processed) > 500:
            processed = processed[:500] + "..."
        
        return processed
    
    async def generate_emotion_response(
        self,
        user_message: str,
        detected_emotion: str,
        user_info: Dict[str, Any],
        emotion_history: List[Dict[str, Any]] = None
    ) -> str:
        """
        감정 기반 맞춤 응답 생성
        
        Args:
            user_message: 사용자 메시지
            detected_emotion: 감지된 감정
            user_info: 사용자 정보
            emotion_history: 감정 기록
            
        Returns:
            str: 감정 맞춤 응답
        """
        try:
            # 감정별 응답 전략
            emotion_strategies = {
                "sad": "위로와 공감을 표현하고, 긍정적인 관점을 제시하세요.",
                "angry": "감정을 이해하고 차분하게 달래주세요.",
                "anxious": "불안감을 덜어주고 안정감을 주는 말을 하세요.",
                "happy": "기쁨을 함께 나누고 더 긍정적인 에너지를 주세요.",
                "lonely": "동반자가 되어주고 따뜻한 관심을 표현하세요.",
                "frustrated": "이해하고 격려하며 해결책을 제시하세요."
            }
            
            strategy = emotion_strategies.get(detected_emotion, "공감하고 지지해주세요.")
            
            # 감정 기반 시스템 프롬프트
            system_prompt = f"""당신은 고령층을 위한 감정 지원 AI입니다.
사용자가 현재 '{detected_emotion}' 감정을 느끼고 있습니다.

대응 전략: {strategy}

사용자 정보:
- 이름: {user_info.get('name', '사용자')}님
- 나이: {user_info.get('age', '미상')}세

감정 상태를 고려하여 따뜻하고 적절한 응답을 해주세요."""
            
            # 감정 기록이 있으면 패턴 분석
            if emotion_history:
                recent_emotions = [e.get('emotion') for e in emotion_history[-5:]]
                if recent_emotions.count(detected_emotion) > 2:
                    system_prompt += f"\n\n주의: 사용자가 최근 '{detected_emotion}' 감정을 자주 느끼고 있습니다. 더 세심한 관심이 필요합니다."
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ]
            
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=300,
                temperature=0.8
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"감정 응답 생성 실패: {str(e)}")
            return "따뜻한 마음으로 함께 있겠습니다. 언제든 이야기해주세요."
    
    async def generate_interest_response(
        self,
        user_message: str,
        user_interests: List[str],
        user_info: Dict[str, Any]
    ) -> str:
        """
        관심사 기반 맞춤 응답 생성
        
        Args:
            user_message: 사용자 메시지
            user_interests: 사용자 관심사
            user_info: 사용자 정보
            
        Returns:
            str: 관심사 맞춤 응답
        """
        try:
            interests_text = ", ".join(user_interests)
            
            system_prompt = f"""당신은 고령층을 위한 AI 동반자입니다.
사용자의 관심사를 활용하여 대화를 이어가세요.

사용자 정보:
- 이름: {user_info.get('name', '사용자')}님
- 관심사: {interests_text}

사용자의 관심사와 연관지어 자연스럽고 흥미로운 대화를 만들어주세요."""
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ]
            
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=300,
                temperature=0.7
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"관심사 응답 생성 실패: {str(e)}")
            return "흥미로운 이야기네요. 더 자세히 들려주세요."
    
    async def generate_summary_response(
        self,
        conversation_history: List[Dict[str, Any]],
        user_info: Dict[str, Any]
    ) -> str:
        """
        대화 요약 생성
        
        Args:
            conversation_history: 대화 기록
            user_info: 사용자 정보
            
        Returns:
            str: 대화 요약
        """
        try:
            # 대화 내용 구성
            conversation_text = "\n".join([
                f"{msg.get('role', 'user')}: {msg.get('content', '')}"
                for msg in conversation_history[-20:]  # 최근 20개
            ])
            
            system_prompt = f"""다음 대화를 요약해주세요.
사용자: {user_info.get('name', '사용자')}님

주요 내용, 감정 상태, 관심사 등을 포함하여 간단히 요약해주세요."""
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": conversation_text}
            ]
            
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=200,
                temperature=0.5
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"대화 요약 생성 실패: {str(e)}")
            return "대화 요약을 생성할 수 없습니다."
    
    async def health_check(self) -> Dict[str, Any]:
        """
        GPT 서비스 상태 확인
        
        Returns:
            Dict[str, Any]: 상태 정보
        """
        try:
            # 간단한 테스트 요청
            test_response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "당신은 테스트 AI입니다."},
                    {"role": "user", "content": "안녕하세요"}
                ],
                max_tokens=50
            )
            
            return {
                "status": "healthy",
                "model": self.model,
                "max_tokens": self.max_tokens,
                "temperature": self.temperature,
                "test_response": test_response.choices[0].message.content
            }
            
        except Exception as e:
            logger.error(f"GPT 서비스 상태 확인 실패: {str(e)}")
            return {
                "status": "unhealthy",
                "error": str(e)
            }

# 전역 GPT 서비스 인스턴스
gpt_service = GPTService()

# 편의 함수들
async def generate_chat_response(
    user_message: str,
    user_info: Dict[str, Any],
    context: ChatPromptContext,
    conversation_history: List[Dict[str, Any]] = None
) -> ChatResponse:
    """채팅 응답 생성"""
    return await gpt_service.generate_response(
        user_message, user_info, context, conversation_history
    )

async def generate_emotion_based_response(
    user_message: str,
    detected_emotion: str,
    user_info: Dict[str, Any]
) -> str:
    """감정 기반 응답 생성"""
    return await gpt_service.generate_emotion_response(
        user_message, detected_emotion, user_info
    ) 