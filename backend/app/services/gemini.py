"""
Gemini 프롬프트 구성 및 응답 생성 서비스 모듈

사용자 정보와 대화 컨텍스트를 기반으로 개인화된 Gemini 응답을 생성합니다.
"""

from typing import List, Dict, Any, Optional, Tuple
import logging
from datetime import datetime
import google.generativeai as genai
from app.config import settings
from app.models.user import User
from app.models.interest import Interest
from app.models.emotion import EmotionSummary
from app.schemas.chat import ChatPromptContext, ChatResponse

logger = logging.getLogger(__name__)

class GeminiService:
    """Gemini 응답 생성 서비스"""
    
    def __init__(self):
        # Gemini API 설정
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
        self.max_tokens = 2000
        self.temperature = 0.7
        
        # 생성 설정
        self.generation_config = genai.GenerationConfig(
            temperature=self.temperature,
            max_output_tokens=self.max_tokens,
            candidate_count=1
        )
        
    async def generate_response(
        self,
        user_message: str,
        user_info: Dict[str, Any],
        context: ChatPromptContext,
        conversation_history: List[Dict[str, Any]] = None
    ) -> ChatResponse:
        # context가 Pydantic 모델이면 dict로 변환
        if hasattr(context, "dict"):
            context = context.dict()
        # 내부 리스트도 dict로 변환
        if 'similar_conversations' in context:
            context['similar_conversations'] = [c.dict() if hasattr(c, 'dict') else c for c in context['similar_conversations']]
        if 'conversation_history' in context:
            context['conversation_history'] = [c.dict() if hasattr(c, 'dict') else c for c in context['conversation_history']]
        try:
            # 시스템 프롬프트 구성
            system_prompt = self._build_system_prompt(user_info, context)
            
            # 대화 히스토리와 함께 완전한 프롬프트 구성
            full_prompt = self._build_conversation_prompt(
                system_prompt, user_message, conversation_history
            )
            
            # Gemini API 호출
            response = await self._generate_content_async(full_prompt)
            
            # 응답 텍스트 추출
            response_text = response.text if response else ""
            
            # 응답 후처리
            processed_response = self._post_process_response(
                response_text, user_info
            )
            
            # 토큰 사용량 정보 (Gemini는 정확한 토큰 카운트를 제공하지 않으므로 추정)
            usage_info = {
                "prompt_tokens": len(full_prompt.split()) * 1.3,  # 대략적인 추정
                "completion_tokens": len(response_text.split()) * 1.3,
                "total_tokens": len(full_prompt.split() + response_text.split()) * 1.3
            }
            
            logger.info(f"Gemini 응답 생성 완료 - 사용자: {user_info.get('user_id')}, 추정 토큰: {int(usage_info['total_tokens'])}")
            
            return ChatResponse(
                session_id=user_info.get('session_id', 'test-session'),
                response=processed_response,
                created_at=datetime.now(),
                model_used="gemini-2.0-flash-exp",
                context_used=[conv.get('message', '') for conv in context.get('similar_conversations', [])],
                similar_conversations=[],
                suggested_actions=[],
                emotion=None,
                emotion_score=None,
                response_time_ms=None
            )
            
        except Exception as e:
            logger.error(f"Gemini 응답 생성 실패: {str(e)}")
            # 기본 응답 반환
            return ChatResponse(
                session_id=user_info.get('session_id', 'error-session'),
                response="죄송합니다. 지금은 응답을 생성할 수 없습니다. 잠시 후 다시 시도해주세요.",
                created_at=datetime.now(),
                model_used="gemini-2.0-flash-exp",
                context_used=[],
                similar_conversations=[],
                suggested_actions=[],
                emotion=None,
                emotion_score=None,
                response_time_ms=None
            )
    
    async def _generate_content_async(self, prompt: str):
        """Gemini API 비동기 호출"""
        try:
            response = self.model.generate_content(
                prompt,
                generation_config=self.generation_config
            )
            return response
        except Exception as e:
            logger.error(f"Gemini API 호출 실패: {str(e)}")
            return None
    
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
        if context.get('user_interests'):
            interests_text = ", ".join(context['user_interests'])
            base_prompt += f"\n\n사용자의 관심사: {interests_text}"
            base_prompt += "\n대화 중에 이런 관심사들을 자연스럽게 언급해보세요."
        
        # 최근 감정 상태 반영
        if context.get('recent_emotions'):
            emotions_text = ", ".join(context['recent_emotions'])
            base_prompt += f"\n\n최근 감정 상태: {emotions_text}"
            base_prompt += "\n사용자의 감정 상태를 고려하여 적절한 위로나 격려를 해주세요."
        
        # 유사한 과거 대화 컨텍스트 활용
        if context.get('similar_conversations'):
            base_prompt += "\n\n과거 비슷한 대화 내용:"
            for i, conv in enumerate(context['similar_conversations'][:3]):  # 최대 3개만
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
    
    def _build_conversation_prompt(
        self,
        system_prompt: str,
        user_message: str,
        conversation_history: List[Dict[str, Any]] = None
    ) -> str:
        """
        대화 프롬프트 구성 (Gemini는 단일 프롬프트 방식)
        
        Args:
            system_prompt: 시스템 프롬프트
            user_message: 사용자 메시지
            conversation_history: 대화 기록
            
        Returns:
            str: 완전한 프롬프트
        """
        prompt = system_prompt + "\n\n"
        
        # 최근 대화 기록 추가 (최대 10개)
        if conversation_history:
            prompt += "최근 대화 기록:\n"
            for msg in conversation_history[-10:]:
                role = "사용자" if msg.get("role") == "user" else "AI"
                content = msg.get("content", "")
                prompt += f"{role}: {content}\n"
            prompt += "\n"
        
        # 현재 사용자 메시지
        prompt += f"사용자: {user_message}\n\n"
        prompt += "AI:"
        
        return prompt
    
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
            return "죄송합니다. 응답을 생성하지 못했습니다."
        
        # 기본 정제
        processed = response_text.strip()
        
        # "AI:" 제거 (혹시 응답에 포함된 경우)
        if processed.startswith("AI:"):
            processed = processed[3:].strip()
        
        # 너무 긴 응답 제한 (500자)
        if len(processed) > 500:
            processed = processed[:500] + "..."
        
        # 사용자 이름으로 개인화 (옵션)
        user_name = user_info.get('name')
        if user_name and len(processed) > 50:
            # 가끔 이름을 자연스럽게 추가
            if "님" not in processed and len(processed) < 200:
                processed = f"{user_name}님, " + processed
        
        return processed
    
    async def generate_emotion_response(
        self,
        user_message: str,
        detected_emotion: str,
        user_info: Dict[str, Any],
        emotion_history: List[Dict[str, Any]] = None
    ) -> str:
        """
        감정 기반 응답 생성
        
        Args:
            user_message: 사용자 메시지
            detected_emotion: 감지된 감정
            user_info: 사용자 정보
            emotion_history: 감정 기록
            
        Returns:
            str: 감정 맞춤 응답
        """
        try:
            user_name = user_info.get('name', '사용자')
            
            # 감정별 프롬프트 구성
            emotion_prompts = {
                "happy": f"사용자가 기쁘고 즐거운 상태입니다. {user_name}님의 기쁨을 함께 나누고 축하해주세요.",
                "sad": f"사용자가 슬프고 우울한 상태입니다. {user_name}님을 따뜻하게 위로하고 공감해주세요.",
                "angry": f"사용자가 화가 나고 짜증난 상태입니다. {user_name}님의 마음을 진정시키고 이해해주세요.",
                "anxious": f"사용자가 불안하고 걱정이 많은 상태입니다. {user_name}님을 안심시키고 격려해주세요.",
                "lonely": f"사용자가 외롭고 쓸쓸한 상태입니다. {user_name}님과 따뜻한 대화로 마음을 달래주세요.",
                "excited": f"사용자가 흥미롭고 신난 상태입니다. {user_name}님의 흥미를 공유하고 함께 즐거워해주세요.",
                "tired": f"사용자가 피곤하고 지친 상태입니다. {user_name}님의 피로를 이해하고 휴식을 권해주세요.",
                "confused": f"사용자가 혼란스럽고 어리둥절한 상태입니다. {user_name}님을 차근차근 도와주세요."
            }
            
            base_prompt = f"""당신은 고령층을 위한 따뜻한 AI 동반자입니다.
{emotion_prompts.get(detected_emotion, f"사용자의 감정 상태에 맞춰 적절히 응답해주세요.")}

사용자 메시지: "{user_message}"

응답 원칙:
- 존댓말 사용
- 감정에 공감하며 따뜻하게 응답
- 100자 내외의 간결한 응답
- 구체적이고 실질적인 조언이나 위로"""
            
            # 감정 기록이 있다면 패턴 반영
            if emotion_history:
                recent_emotions = [h.get('emotion', '') for h in emotion_history[-5:]]
                if recent_emotions:
                    base_prompt += f"\n최근 감정 패턴: {', '.join(recent_emotions)}"
                    base_prompt += "\n이런 감정 변화를 고려하여 응답해주세요."
            
            response = await self._generate_content_async(base_prompt)
            
            if response and response.text:
                return self._post_process_response(response.text, user_info)
            else:
                return f"{user_name}님의 마음을 이해합니다. 언제든 저와 대화해주세요."
                
        except Exception as e:
            logger.error(f"Gemini 감정 응답 생성 실패: {str(e)}")
            return "마음이 힘드시군요. 제가 옆에 있으니 언제든 이야기해주세요."
    
    async def generate_interest_response(
        self,
        user_message: str,
        user_interests: List[str],
        user_info: Dict[str, Any]
    ) -> str:
        """
        관심사 기반 응답 생성
        
        Args:
            user_message: 사용자 메시지
            user_interests: 사용자 관심사 리스트
            user_info: 사용자 정보
            
        Returns:
            str: 관심사 맞춤 응답
        """
        try:
            user_name = user_info.get('name', '사용자')
            interests_text = ", ".join(user_interests) if user_interests else "다양한 활동"
            
            prompt = f"""당신은 고령층을 위한 친근한 AI 동반자입니다.
사용자의 관심사를 바탕으로 대화를 이어가세요.

사용자 정보:
- 이름: {user_name}님
- 관심사: {interests_text}

사용자 메시지: "{user_message}"

응답 원칙:
- 사용자의 관심사와 연결하여 자연스럽게 대화
- 관심사 관련 질문이나 제안을 포함
- 존댓말 사용
- 150자 내외의 적절한 길이
- 긍정적이고 격려하는 톤"""
            
            response = await self._generate_content_async(prompt)
            
            if response and response.text:
                return self._post_process_response(response.text, user_info)
            else:
                return f"{user_name}님의 {interests_text}에 대한 이야기를 더 들려주세요!"
                
        except Exception as e:
            logger.error(f"Gemini 관심사 응답 생성 실패: {str(e)}")
            return f"{user_name}님의 취미 이야기를 더 들어보고 싶어요. 자세히 말씀해주세요!"
    
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
            if not conversation_history:
                return "오늘은 대화가 없었습니다."
            
            # 대화 내용 구성
            conversation_text = ""
            for msg in conversation_history[-20:]:  # 최근 20개 메시지
                role = "사용자" if msg.get("role") == "user" else "AI"
                content = msg.get("content", "")
                conversation_text += f"{role}: {content}\n"
            
            user_name = user_info.get('name', '사용자')
            
            prompt = f"""다음은 {user_name}님과의 대화 내용입니다. 이를 요약해주세요.

대화 내용:
{conversation_text}

요약 원칙:
- 주요 대화 주제와 내용을 간단히 정리
- 사용자의 감정 상태나 관심사 언급
- 100자 내외로 요약
- 따뜻하고 친근한 톤 유지"""
            
            response = await self._generate_content_async(prompt)
            
            if response and response.text:
                return self._post_process_response(response.text, user_info)
            else:
                return f"{user_name}님과 즐거운 대화를 나누었습니다."
                
        except Exception as e:
            logger.error(f"Gemini 대화 요약 생성 실패: {str(e)}")
            return "오늘도 좋은 대화였습니다."
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Gemini API 상태 확인
        
        Returns:
            Dict[str, Any]: 상태 정보
        """
        try:
            test_response = await self._generate_content_async("안녕하세요")
            
            if test_response and test_response.text:
                return {
                    "status": "healthy",
                    "model": "gemini-2.0-flash-exp",
                    "api_accessible": True,
                    "test_response_length": len(test_response.text)
                }
            else:
                return {
                    "status": "unhealthy",
                    "model": "gemini-2.0-flash-exp",
                    "api_accessible": False,
                    "error": "No response received"
                }
                
        except Exception as e:
            return {
                "status": "unhealthy",
                "model": "gemini-2.0-flash-exp",
                "api_accessible": False,
                "error": str(e)
            }


# 전역 서비스 인스턴스
gemini_service = GeminiService()


# 헬퍼 함수들 (기존 GPT 서비스와 호환성을 위해)
async def generate_chat_response(
    user_message: str,
    user_info: Dict[str, Any],
    context: ChatPromptContext,
    conversation_history: List[Dict[str, Any]] = None
) -> ChatResponse:
    """채팅 응답 생성 (GPT 서비스 호환)"""
    return await gemini_service.generate_response(
        user_message, user_info, context, conversation_history
    )


async def generate_emotion_based_response(
    user_message: str,
    detected_emotion: str,
    user_info: Dict[str, Any]
) -> str:
    """감정 기반 응답 생성 (GPT 서비스 호환)"""
    return await gemini_service.generate_emotion_response(
        user_message, detected_emotion, user_info
    ) 