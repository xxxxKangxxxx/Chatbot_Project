"""
사용자 맞춤화 서비스 모듈

사용자의 관심사, 말투, 성격 등을 추적하고 개인화된 경험을 제공합니다.
"""

from typing import List, Dict, Any, Optional, Tuple
import logging
from datetime import datetime, timedelta
from collections import Counter
import re
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.crud.user import get_user_by_id, update_user
from app.crud.chat_log import get_user_chat_history
from app.schemas.user import UserProfileUpdate, PersonalityTraits
from app.schemas.interest import InterestCategoryEnum

logger = logging.getLogger(__name__)

class UserProfileService:
    """사용자 프로필 맞춤화 서비스"""
    
    def __init__(self):
        # 관심사 키워드 사전
        self.interest_keywords = {
            "gardening": ["정원", "화분", "꽃", "식물", "원예", "가드닝", "씨앗", "물주기", "비료", "화초"],
            "cooking": ["요리", "음식", "레시피", "요리법", "조리", "맛", "재료", "조미료", "국", "찌개"],
            "reading": ["책", "독서", "소설", "읽기", "도서", "글", "작가", "문학", "시", "잡지"],
            "walking": ["산책", "걷기", "운동", "건강", "공원", "길", "운동화", "헬스", "체력", "활동"],
            "music": ["음악", "노래", "가요", "클래식", "악기", "피아노", "기타", "트로트", "발라드", "멜로디"],
            "family": ["가족", "자녀", "손자", "손녀", "딸", "아들", "며느리", "사위", "부모", "형제"],
            "travel": ["여행", "관광", "구경", "나들이", "여행지", "관광지", "풍경", "사진", "추억", "경치"],
            "health": ["건강", "병원", "약", "운동", "몸", "아프", "치료", "의사", "검사", "관리"],
            "pets": ["반려동물", "강아지", "고양이", "애완동물", "펫", "개", "고양이", "새", "물고기", "햄스터"],
            "crafts": ["만들기", "공예", "손작업", "뜨개질", "바느질", "그림", "그리기", "취미", "창작", "예술"],
            "technology": ["컴퓨터", "스마트폰", "인터넷", "카카오톡", "유튜브", "앱", "디지털", "온라인", "핸드폰", "전화"],
            "food": ["음식", "맛집", "식당", "밥", "국", "찌개", "반찬", "김치", "된장", "고추장"],
            "weather": ["날씨", "비", "눈", "바람", "더위", "추위", "봄", "여름", "가을", "겨울"],
            "neighborhood": ["동네", "이웃", "마을", "아파트", "집", "근처", "주변", "시장", "상점", "마트"]
        }
        
        # 말투 패턴 분석
        self.tone_patterns = {
            "formal": ["습니다", "입니다", "하겠습니다", "드립니다", "께서", "하시"],
            "informal": ["해요", "예요", "이에요", "해", "야", "지"],
            "polite": ["죄송", "감사", "고마", "실례", "부탁", "양해"],
            "casual": ["그냥", "막", "좀", "진짜", "완전", "너무"],
            "emotional": ["정말", "진짜", "아", "어", "우", "이런", "저런", "그런"]
        }
        
        # 성격 특성 키워드
        self.personality_keywords = {
            "outgoing": ["사람", "만나", "이야기", "대화", "친구", "모임", "활발", "외향"],
            "introverted": ["혼자", "조용", "차분", "내성", "집", "책", "생각", "내향"],
            "optimistic": ["긍정", "희망", "좋", "밝", "즐거", "행복", "웃", "기쁨"],
            "pessimistic": ["걱정", "불안", "힘들", "어려", "문제", "부정", "우울", "슬픔"],
            "patient": ["천천히", "기다", "참", "여유", "느긋", "차근차근", "점진적", "인내"],
            "impatient": ["빨리", "급", "답답", "서두", "바로", "즉시", "성급", "조급"],
            "detail_oriented": ["자세히", "꼼꼼", "정확", "세밀", "구체적", "디테일", "완벽", "정밀"],
            "big_picture": ["전체", "대략", "개략", "큰", "전반", "일반", "포괄", "광범위"]
        }
    
    async def analyze_user_interests(
        self,
        user_id: str,
        chat_history: List[Dict[str, Any]],
        days_back: int = 30
    ) -> Dict[str, Any]:
        """
        사용자 관심사 분석
        
        Args:
            user_id: 사용자 ID
            chat_history: 채팅 기록
            days_back: 분석할 과거 일수
            
        Returns:
            Dict[str, Any]: 관심사 분석 결과
        """
        try:
            # 최근 대화 필터링
            cutoff_date = datetime.now() - timedelta(days=days_back)
            recent_chats = [
                chat for chat in chat_history
                if chat.get('timestamp', datetime.now()) >= cutoff_date
            ]
            
            if not recent_chats:
                return {"interests": {}, "confidence": 0.0}
            
            # 모든 메시지 텍스트 결합
            all_text = " ".join([
                chat.get('message', '') for chat in recent_chats
                if chat.get('role') == 'user'
            ])
            
            # 관심사별 점수 계산
            interest_scores = {}
            for interest, keywords in self.interest_keywords.items():
                score = 0
                for keyword in keywords:
                    matches = len(re.findall(keyword, all_text, re.IGNORECASE))
                    score += matches
                
                if score > 0:
                    # 정규화 (메시지 수로 나누기)
                    normalized_score = score / len(recent_chats)
                    interest_scores[interest] = min(normalized_score, 1.0)
            
            # 상위 관심사 선택
            top_interests = dict(sorted(
                interest_scores.items(), 
                key=lambda x: x[1], 
                reverse=True
            )[:5])
            
            # 신뢰도 계산
            confidence = self._calculate_interest_confidence(top_interests, len(recent_chats))
            
            logger.info(f"관심사 분석 완료 - 사용자: {user_id}, 상위 관심사: {list(top_interests.keys())}")
            
            return {
                "interests": top_interests,
                "confidence": confidence,
                "analysis_period": days_back,
                "analyzed_messages": len(recent_chats),
                "timestamp": datetime.now()
            }
            
        except Exception as e:
            logger.error(f"관심사 분석 실패: {str(e)}")
            return {"interests": {}, "confidence": 0.0, "error": str(e)}
    
    def _calculate_interest_confidence(self, interests: Dict[str, float], message_count: int) -> float:
        """관심사 분석 신뢰도 계산"""
        if not interests or message_count < 5:
            return 0.0
        
        # 메시지 수가 많을수록 신뢰도 증가
        message_factor = min(message_count / 50, 1.0)
        
        # 관심사 점수 분포가 명확할수록 신뢰도 증가
        scores = list(interests.values())
        if len(scores) > 1:
            score_variance = max(scores) - min(scores)
            variance_factor = min(score_variance, 1.0)
        else:
            variance_factor = 0.5
        
        confidence = (message_factor + variance_factor) / 2
        return round(confidence, 2)
    
    async def analyze_communication_style(
        self,
        user_id: str,
        chat_history: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        사용자 소통 스타일 분석
        
        Args:
            user_id: 사용자 ID
            chat_history: 채팅 기록
            
        Returns:
            Dict[str, Any]: 소통 스타일 분석 결과
        """
        try:
            # 사용자 메시지만 추출
            user_messages = [
                chat.get('message', '') for chat in chat_history
                if chat.get('role') == 'user'
            ]
            
            if not user_messages:
                return {"style": "unknown", "confidence": 0.0}
            
            all_text = " ".join(user_messages)
            
            # 말투 패턴 분석
            tone_scores = {}
            for tone, patterns in self.tone_patterns.items():
                score = 0
                for pattern in patterns:
                    matches = len(re.findall(pattern, all_text, re.IGNORECASE))
                    score += matches
                
                if score > 0:
                    tone_scores[tone] = score / len(user_messages)
            
            # 메시지 특성 분석
            avg_length = sum(len(msg) for msg in user_messages) / len(user_messages)
            question_ratio = sum(1 for msg in user_messages if '?' in msg) / len(user_messages)
            exclamation_ratio = sum(1 for msg in user_messages if '!' in msg) / len(user_messages)
            
            # 주요 말투 선택
            preferred_tone = max(tone_scores.keys(), key=lambda k: tone_scores[k]) if tone_scores else "neutral"
            
            # 소통 스타일 특성
            communication_traits = {
                "preferred_tone": preferred_tone,
                "tone_scores": tone_scores,
                "avg_message_length": round(avg_length, 1),
                "question_ratio": round(question_ratio, 2),
                "exclamation_ratio": round(exclamation_ratio, 2),
                "formality_level": self._determine_formality_level(tone_scores),
                "emotional_expressiveness": self._determine_emotional_level(tone_scores, exclamation_ratio)
            }
            
            logger.info(f"소통 스타일 분석 완료 - 사용자: {user_id}, 선호 말투: {preferred_tone}")
            
            return {
                "style": preferred_tone,
                "traits": communication_traits,
                "confidence": self._calculate_style_confidence(tone_scores, len(user_messages)),
                "analyzed_messages": len(user_messages),
                "timestamp": datetime.now()
            }
            
        except Exception as e:
            logger.error(f"소통 스타일 분석 실패: {str(e)}")
            return {"style": "unknown", "confidence": 0.0, "error": str(e)}
    
    def _determine_formality_level(self, tone_scores: Dict[str, float]) -> str:
        """격식 수준 결정"""
        formal_score = tone_scores.get('formal', 0)
        informal_score = tone_scores.get('informal', 0)
        
        if formal_score > informal_score * 1.5:
            return "high"
        elif informal_score > formal_score * 1.5:
            return "low"
        else:
            return "medium"
    
    def _determine_emotional_level(self, tone_scores: Dict[str, float], exclamation_ratio: float) -> str:
        """감정 표현 수준 결정"""
        emotional_score = tone_scores.get('emotional', 0)
        
        if emotional_score > 0.3 or exclamation_ratio > 0.2:
            return "high"
        elif emotional_score > 0.1 or exclamation_ratio > 0.1:
            return "medium"
        else:
            return "low"
    
    def _calculate_style_confidence(self, tone_scores: Dict[str, float], message_count: int) -> float:
        """스타일 분석 신뢰도 계산"""
        if message_count < 5:
            return 0.0
        
        # 메시지 수 기반 신뢰도
        message_factor = min(message_count / 30, 1.0)
        
        # 말투 패턴 명확성
        if tone_scores:
            max_score = max(tone_scores.values())
            pattern_factor = min(max_score, 1.0)
        else:
            pattern_factor = 0.0
        
        confidence = (message_factor + pattern_factor) / 2
        return round(confidence, 2)
    
    async def analyze_personality_traits(
        self,
        user_id: str,
        chat_history: List[Dict[str, Any]],
        emotion_history: List[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        성격 특성 분석
        
        Args:
            user_id: 사용자 ID
            chat_history: 채팅 기록
            emotion_history: 감정 기록
            
        Returns:
            Dict[str, Any]: 성격 특성 분석 결과
        """
        try:
            # 사용자 메시지 추출
            user_messages = [
                chat.get('message', '') for chat in chat_history
                if chat.get('role') == 'user'
            ]
            
            if not user_messages:
                return {"traits": {}, "confidence": 0.0}
            
            all_text = " ".join(user_messages)
            
            # 성격 특성 키워드 분석
            trait_scores = {}
            for trait, keywords in self.personality_keywords.items():
                score = 0
                for keyword in keywords:
                    matches = len(re.findall(keyword, all_text, re.IGNORECASE))
                    score += matches
                
                if score > 0:
                    trait_scores[trait] = score / len(user_messages)
            
            # 감정 기록 기반 성격 분석
            if emotion_history:
                emotion_traits = self._analyze_personality_from_emotions(emotion_history)
                # 감정 기반 특성과 키워드 기반 특성 결합
                for trait, score in emotion_traits.items():
                    if trait in trait_scores:
                        trait_scores[trait] = (trait_scores[trait] + score) / 2
                    else:
                        trait_scores[trait] = score
            
            # 상위 특성 선택
            top_traits = dict(sorted(
                trait_scores.items(), 
                key=lambda x: x[1], 
                reverse=True
            )[:5])
            
            # 성격 프로필 생성
            personality_profile = self._generate_personality_profile(top_traits)
            
            logger.info(f"성격 분석 완료 - 사용자: {user_id}, 주요 특성: {list(top_traits.keys())}")
            
            return {
                "traits": top_traits,
                "profile": personality_profile,
                "confidence": self._calculate_personality_confidence(top_traits, len(user_messages)),
                "analyzed_messages": len(user_messages),
                "timestamp": datetime.now()
            }
            
        except Exception as e:
            logger.error(f"성격 분석 실패: {str(e)}")
            return {"traits": {}, "confidence": 0.0, "error": str(e)}
    
    def _analyze_personality_from_emotions(self, emotion_history: List[Dict[str, Any]]) -> Dict[str, float]:
        """감정 기록으로부터 성격 특성 분석"""
        emotion_traits = {}
        
        if not emotion_history:
            return emotion_traits
        
        # 감정 분포 계산
        emotion_counts = Counter(emotion.get('emotion', 'neutral') for emotion in emotion_history)
        total_emotions = len(emotion_history)
        
        # 감정 기반 성격 특성 추론
        if emotion_counts.get('happy', 0) / total_emotions > 0.3:
            emotion_traits['optimistic'] = 0.7
        
        if emotion_counts.get('sad', 0) / total_emotions > 0.3:
            emotion_traits['pessimistic'] = 0.6
        
        if emotion_counts.get('anxious', 0) / total_emotions > 0.2:
            emotion_traits['cautious'] = 0.6
        
        if emotion_counts.get('excited', 0) / total_emotions > 0.2:
            emotion_traits['outgoing'] = 0.6
        
        if emotion_counts.get('lonely', 0) / total_emotions > 0.2:
            emotion_traits['introverted'] = 0.5
        
        # 감정 변화 패턴 분석
        if len(set(emotion_counts.keys())) > 5:
            emotion_traits['emotionally_expressive'] = 0.7
        
        return emotion_traits
    
    def _generate_personality_profile(self, traits: Dict[str, float]) -> Dict[str, Any]:
        """성격 프로필 생성"""
        profile = {
            "primary_traits": [],
            "secondary_traits": [],
            "description": "",
            "communication_preferences": []
        }
        
        # 주요 특성과 부차적 특성 분류
        sorted_traits = sorted(traits.items(), key=lambda x: x[1], reverse=True)
        
        if len(sorted_traits) >= 1:
            profile["primary_traits"] = [sorted_traits[0][0]]
        
        if len(sorted_traits) >= 3:
            profile["secondary_traits"] = [trait[0] for trait in sorted_traits[1:3]]
        
        # 성격 설명 생성
        if 'optimistic' in traits:
            profile["description"] += "긍정적이고 밝은 성격, "
        if 'introverted' in traits:
            profile["description"] += "내향적이고 신중한 성격, "
        if 'outgoing' in traits:
            profile["description"] += "외향적이고 활발한 성격, "
        if 'patient' in traits:
            profile["description"] += "인내심이 많고 차분한 성격, "
        
        profile["description"] = profile["description"].rstrip(", ")
        
        # 소통 선호도 추론
        if 'outgoing' in traits:
            profile["communication_preferences"].append("활발한 대화를 선호")
        if 'introverted' in traits:
            profile["communication_preferences"].append("깊이 있는 대화를 선호")
        if 'patient' in traits:
            profile["communication_preferences"].append("천천히 진행되는 대화를 선호")
        
        return profile
    
    def _calculate_personality_confidence(self, traits: Dict[str, float], message_count: int) -> float:
        """성격 분석 신뢰도 계산"""
        if message_count < 10:
            return 0.0
        
        # 메시지 수 기반 신뢰도
        message_factor = min(message_count / 50, 1.0)
        
        # 특성 점수 분포
        if traits:
            max_score = max(traits.values())
            trait_factor = min(max_score, 1.0)
        else:
            trait_factor = 0.0
        
        confidence = (message_factor + trait_factor) / 2
        return round(confidence, 2)
    
    async def generate_personalized_recommendations(
        self,
        user_id: str,
        interests: Dict[str, float],
        personality_traits: Dict[str, float],
        communication_style: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        개인화된 추천 생성
        
        Args:
            user_id: 사용자 ID
            interests: 관심사 정보
            personality_traits: 성격 특성
            communication_style: 소통 스타일
            
        Returns:
            Dict[str, Any]: 개인화 추천 결과
        """
        try:
            recommendations = {
                "conversation_topics": [],
                "interaction_style": {},
                "content_preferences": [],
                "activity_suggestions": []
            }
            
            # 대화 주제 추천
            for interest, score in sorted(interests.items(), key=lambda x: x[1], reverse=True)[:3]:
                topic_suggestions = self._get_topic_suggestions(interest)
                recommendations["conversation_topics"].extend(topic_suggestions)
            
            # 상호작용 스타일 추천
            preferred_tone = communication_style.get('style', 'neutral')
            formality_level = communication_style.get('traits', {}).get('formality_level', 'medium')
            
            recommendations["interaction_style"] = {
                "preferred_tone": preferred_tone,
                "formality_level": formality_level,
                "response_length": "medium" if communication_style.get('traits', {}).get('avg_message_length', 50) > 30 else "short",
                "emotional_support_level": "high" if 'pessimistic' in personality_traits else "medium"
            }
            
            # 콘텐츠 선호도
            if 'reading' in interests:
                recommendations["content_preferences"].append("텍스트 기반 정보 제공")
            if 'technology' in interests:
                recommendations["content_preferences"].append("디지털 콘텐츠 활용")
            if 'visual' in interests:
                recommendations["content_preferences"].append("시각적 콘텐츠 선호")
            
            # 활동 제안
            activity_suggestions = self._generate_activity_suggestions(interests, personality_traits)
            recommendations["activity_suggestions"] = activity_suggestions
            
            logger.info(f"개인화 추천 생성 완료 - 사용자: {user_id}")
            
            return {
                "recommendations": recommendations,
                "personalization_score": self._calculate_personalization_score(interests, personality_traits),
                "timestamp": datetime.now()
            }
            
        except Exception as e:
            logger.error(f"개인화 추천 생성 실패: {str(e)}")
            return {"recommendations": {}, "error": str(e)}
    
    def _get_topic_suggestions(self, interest: str) -> List[str]:
        """관심사별 대화 주제 제안"""
        topic_map = {
            "gardening": ["요즘 기르시는 식물이 있나요?", "좋아하시는 꽃이 있나요?", "정원 가꾸기는 어떠세요?"],
            "cooking": ["오늘은 어떤 음식을 드셨나요?", "좋아하시는 요리가 있나요?", "요리하는 것을 좋아하시나요?"],
            "reading": ["요즘 읽고 계신 책이 있나요?", "좋아하시는 작가가 있나요?", "어떤 종류의 책을 좋아하시나요?"],
            "walking": ["오늘 산책하셨나요?", "좋아하시는 산책로가 있나요?", "운동은 어떻게 하고 계시나요?"],
            "music": ["좋아하시는 음악이 있나요?", "어떤 가수를 좋아하시나요?", "음악 들으시는 것을 좋아하시나요?"],
            "family": ["가족분들은 어떻게 지내시나요?", "손자손녀들은 잘 지내나요?", "가족 모임은 자주 하시나요?"],
            "health": ["건강은 어떻게 관리하고 계시나요?", "운동은 꾸준히 하고 계시나요?", "병원 검진은 받으셨나요?"]
        }
        
        return topic_map.get(interest, [f"{interest}에 대해 이야기해볼까요?"])
    
    def _generate_activity_suggestions(
        self, 
        interests: Dict[str, float], 
        personality_traits: Dict[str, float]
    ) -> List[str]:
        """활동 제안 생성"""
        suggestions = []
        
        # 관심사 기반 활동 제안
        if 'gardening' in interests:
            suggestions.append("집에서 화분 기르기")
        if 'reading' in interests:
            suggestions.append("도서관 방문하기")
        if 'walking' in interests:
            suggestions.append("공원 산책하기")
        if 'cooking' in interests:
            suggestions.append("새로운 요리 도전하기")
        
        # 성격 기반 활동 제안
        if 'outgoing' in personality_traits:
            suggestions.append("이웃과 대화하기")
            suggestions.append("동호회 참여하기")
        if 'introverted' in personality_traits:
            suggestions.append("혼자만의 시간 갖기")
            suggestions.append("명상이나 요가하기")
        
        return suggestions[:5]  # 최대 5개
    
    def _calculate_personalization_score(
        self, 
        interests: Dict[str, float], 
        personality_traits: Dict[str, float]
    ) -> float:
        """개인화 점수 계산"""
        interest_score = len(interests) * 0.2
        trait_score = len(personality_traits) * 0.15
        
        # 점수 합계와 신뢰도
        total_score = interest_score + trait_score
        personalization_score = min(total_score, 1.0)
        
        return round(personalization_score, 2)
    
    async def update_user_profile_from_analysis(
        self,
        user_id: str,
        interests: Dict[str, float],
        communication_style: Dict[str, Any],
        personality_traits: Dict[str, float],
        db: AsyncSession
    ) -> bool:
        """
        분석 결과를 바탕으로 사용자 프로필 업데이트
        
        Args:
            user_id: 사용자 ID
            interests: 관심사 분석 결과
            communication_style: 소통 스타일 분석 결과
            personality_traits: 성격 특성 분석 결과
            db: 데이터베이스 세션
            
        Returns:
            bool: 업데이트 성공 여부
        """
        try:
            # 프로필 업데이트 데이터 구성
            profile_update = UserProfileUpdate(
                preferred_tone=communication_style.get('style', 'neutral'),
                personality_traits=list(personality_traits.keys())[:3],  # 상위 3개 특성
                interests=list(interests.keys())[:5],  # 상위 5개 관심사
                communication_preferences={
                    "formality_level": communication_style.get('traits', {}).get('formality_level', 'medium'),
                    "emotional_expressiveness": communication_style.get('traits', {}).get('emotional_expressiveness', 'medium'),
                    "preferred_response_length": "medium"
                }
            )
            
            # 데이터베이스 업데이트
            updated_user = await update_user(db, user_id, profile_update)
            
            if updated_user:
                logger.info(f"사용자 프로필 업데이트 완료 - 사용자: {user_id}")
                return True
            else:
                logger.warning(f"사용자 프로필 업데이트 실패 - 사용자: {user_id}")
                return False
                
        except Exception as e:
            logger.error(f"사용자 프로필 업데이트 중 오류: {str(e)}")
            return False
    
    async def health_check(self) -> Dict[str, Any]:
        """
        사용자 프로필 서비스 상태 확인
        
        Returns:
            Dict[str, Any]: 상태 정보
        """
        try:
            return {
                "status": "healthy",
                "interest_categories": len(self.interest_keywords),
                "tone_patterns": len(self.tone_patterns),
                "personality_traits": len(self.personality_keywords),
                "service_features": [
                    "interest_analysis",
                    "communication_style_analysis", 
                    "personality_analysis",
                    "personalized_recommendations"
                ]
            }
            
        except Exception as e:
            logger.error(f"사용자 프로필 서비스 상태 확인 실패: {str(e)}")
            return {
                "status": "unhealthy",
                "error": str(e)
            }

# 전역 사용자 프로필 서비스 인스턴스
user_profile_service = UserProfileService()

# 편의 함수들
async def analyze_user_profile(
    user_id: str,
    chat_history: List[Dict[str, Any]],
    emotion_history: List[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """사용자 프로필 종합 분석"""
    interests = await user_profile_service.analyze_user_interests(user_id, chat_history)
    communication_style = await user_profile_service.analyze_communication_style(user_id, chat_history)
    personality_traits = await user_profile_service.analyze_personality_traits(user_id, chat_history, emotion_history)
    
    return {
        "interests": interests,
        "communication_style": communication_style,
        "personality_traits": personality_traits,
        "timestamp": datetime.now()
    }

async def get_personalized_recommendations(
    user_id: str,
    interests: Dict[str, float],
    personality_traits: Dict[str, float],
    communication_style: Dict[str, Any]
) -> Dict[str, Any]:
    """개인화된 추천 생성"""
    return await user_profile_service.generate_personalized_recommendations(
        user_id, interests, personality_traits, communication_style
    ) 