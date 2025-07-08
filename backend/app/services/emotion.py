"""
감정 분석 및 감정 요약 서비스 모듈

텍스트에서 감정을 추출하고 감정 요약 데이터를 관리합니다.
"""

from typing import List, Dict, Any, Optional, Tuple
import logging
from datetime import datetime, timedelta
import re
import google.generativeai as genai
from app.config import settings
from app.schemas.emotion import EmotionTypeEnum, EmotionAnalysisResult, EmotionTrendAnalysis

logger = logging.getLogger(__name__)

class EmotionService:
    """감정 분석 및 관리 서비스"""
    
    def __init__(self):
        # Gemini API 설정
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
        
        # 감정 키워드 사전
        self.emotion_keywords = {
            "happy": ["기쁘", "행복", "즐거", "웃", "좋", "만족", "감사", "흥미", "재미", "신나"],
            "sad": ["슬프", "우울", "눈물", "울", "힘들", "괴로", "아프", "외로", "쓸쓸", "허전"],
            "angry": ["화나", "짜증", "분노", "열받", "빡", "억울", "분해", "성가", "귀찮", "불쾌"],
            "anxious": ["불안", "걱정", "두려", "무서", "떨", "긴장", "초조", "조마조마", "근심", "염려"],
            "lonely": ["외로", "혼자", "쓸쓸", "고독", "적적", "허전", "공허", "소외", "그리", "보고싶"],
            "frustrated": ["답답", "막막", "갑갑", "짜증", "스트레스", "피곤", "지쳐", "힘들", "어려", "복잡"],
            "excited": ["설레", "기대", "두근", "흥분", "신나", "들뜨", "활기", "생기", "에너지", "열정"],
            "grateful": ["감사", "고마", "다행", "고맙", "은혜", "도움", "배려", "친절", "따뜻", "정"],
            "worried": ["걱정", "염려", "우려", "근심", "불안", "두려", "조심", "신경", "마음", "생각"],
            "content": ["평온", "안정", "차분", "편안", "고요", "여유", "느긋", "만족", "괜찮", "무난"],
            "calm": ["차분", "평온", "안정", "고요", "여유", "느긋", "만족", "괜찮", "무난"]
        }
    
    async def analyze_emotion(
        self,
        text: str,
        user_id: Optional[str] = None,
        use_ai: bool = True
    ) -> EmotionAnalysisResult:
        """
        텍스트에서 감정 분석
        
        Args:
            text: 분석할 텍스트
            user_id: 사용자 ID
            use_ai: AI 감정 분석 사용 여부
            
        Returns:
            EmotionAnalysisResult: 감정 분석 결과
        """
        try:
            # 키워드 기반 기본 분석
            keyword_emotions = self._analyze_by_keywords(text)
            
            # AI 기반 분석 (선택사항)
            ai_emotions = {}
            if use_ai:
                ai_emotions = await self._analyze_by_ai(text)
            
            # 결과 통합
            final_emotions = self._combine_emotion_results(keyword_emotions, ai_emotions)
            
            # 주요 감정 선택
            primary_emotion = self._get_primary_emotion(final_emotions)
            
            # 감정 강도 계산
            intensity = self._calculate_intensity(text, primary_emotion)
            
            result = EmotionAnalysisResult(
                primary_emotion=primary_emotion,
                emotion_scores=final_emotions,
                intensity=intensity,
                confidence=self._calculate_confidence(final_emotions),
                detected_keywords=self._extract_emotion_keywords(text, primary_emotion),
                analysis_method="hybrid" if use_ai else "keyword",
                timestamp=datetime.now()
            )
            
            logger.info(f"감정 분석 완료 - 사용자: {user_id}, 주요 감정: {primary_emotion}, 강도: {intensity}")
            
            return result
            
        except Exception as e:
            logger.error(f"감정 분석 실패: {str(e)}")
            # 기본 중성 감정 반환
            return EmotionAnalysisResult(
                primary_emotion=EmotionTypeEnum.CALM,
                emotion_scores={"calm": 1.0},
                intensity=0.5,
                confidence=0.3,
                detected_keywords=[],
                analysis_method="fallback",
                timestamp=datetime.now()
            )
    
    def _analyze_by_keywords(self, text: str) -> Dict[str, float]:
        """키워드 기반 감정 분석"""
        emotion_scores = {}
        text_lower = text.lower()
        
        for emotion, keywords in self.emotion_keywords.items():
            score = 0
            for keyword in keywords:
                # 키워드 매칭 (부분 문자열)
                matches = len(re.findall(keyword, text_lower))
                score += matches * 0.1
            
            if score > 0:
                emotion_scores[emotion] = min(score, 1.0)  # 최대 1.0으로 제한
        
        # 감정이 감지되지 않으면 중성
        if not emotion_scores:
            emotion_scores["calm"] = 0.8
        
        return emotion_scores
    
    async def _analyze_by_ai(self, text: str) -> Dict[str, float]:
        """AI 기반 감정 분석"""
        try:
            system_prompt = """당신은 감정 분석 전문가입니다.
주어진 텍스트에서 감정을 분석하고 다음 형식으로 응답해주세요:

감정 종류: happy, sad, angry, anxious, lonely, frustrated, excited, grateful, worried, content, calm

응답 형식:
emotion:score,emotion:score,...

예시: happy:0.8,grateful:0.3,content:0.2

점수는 0.0~1.0 사이의 값으로, 감지된 감정의 강도를 나타냅니다."""
            
            # Gemini용 프롬프트 구성
            full_prompt = f"""{system_prompt}

다음 텍스트의 감정을 분석해주세요: {text}"""
            
            response = self.model.generate_content(
                full_prompt,
                generation_config=genai.GenerationConfig(
                    max_output_tokens=200,
                    temperature=0.3
                )
            )
            
            # 응답 파싱
            response_text = response.text.strip() if response and response.text else ""
            return self._parse_ai_emotion_response(response_text)
            
        except Exception as e:
            logger.error(f"AI 감정 분석 실패: {str(e)}")
            return {}
    
    def _parse_ai_emotion_response(self, response_text: str) -> Dict[str, float]:
        """AI 응답 파싱"""
        emotion_scores = {}
        
        try:
            # "emotion:score" 형식 파싱
            parts = response_text.split(',')
            for part in parts:
                if ':' in part:
                    emotion, score_str = part.strip().split(':')
                    emotion = emotion.strip().lower()
                    score = float(score_str.strip())
                    
                    if 0.0 <= score <= 1.0:
                        emotion_scores[emotion] = score
        except Exception as e:
            logger.error(f"AI 응답 파싱 실패: {str(e)}")
        
        return emotion_scores
    
    def _combine_emotion_results(
        self, 
        keyword_emotions: Dict[str, float], 
        ai_emotions: Dict[str, float]
    ) -> Dict[str, float]:
        """감정 분석 결과 통합"""
        combined = {}
        
        # 키워드 기반 결과 (가중치 0.4)
        for emotion, score in keyword_emotions.items():
            combined[emotion] = score * 0.4
        
        # AI 기반 결과 (가중치 0.6)
        for emotion, score in ai_emotions.items():
            if emotion in combined:
                combined[emotion] += score * 0.6
            else:
                combined[emotion] = score * 0.6
        
        # 정규화 (합이 1.0이 되도록)
        total_score = sum(combined.values())
        if total_score > 0:
            combined = {k: v / total_score for k, v in combined.items()}
        
        return combined
    
    def _get_primary_emotion(self, emotion_scores: Dict[str, float]) -> EmotionTypeEnum:
        """주요 감정 선택"""
        if not emotion_scores:
            return EmotionTypeEnum.CALM
        
        # 가장 높은 점수의 감정 선택
        primary_emotion_str = max(emotion_scores.keys(), key=lambda k: emotion_scores[k])
        
        # EmotionTypeEnum으로 변환
        emotion_mapping = {
            "happy": EmotionTypeEnum.HAPPY,
            "sad": EmotionTypeEnum.SAD,
            "angry": EmotionTypeEnum.ANGRY,
            "anxious": EmotionTypeEnum.ANXIOUS,
            "lonely": EmotionTypeEnum.LONELY,
            "frustrated": EmotionTypeEnum.FRUSTRATED,
            "excited": EmotionTypeEnum.EXCITED,
            "grateful": EmotionTypeEnum.GRATEFUL,
            "worried": EmotionTypeEnum.WORRIED,
            "content": EmotionTypeEnum.CONTENT,
            "calm": EmotionTypeEnum.CALM
        }
        
        return emotion_mapping.get(primary_emotion_str, EmotionTypeEnum.CALM)
    
    def _calculate_intensity(self, text: str, primary_emotion: EmotionTypeEnum) -> float:
        """감정 강도 계산"""
        # 텍스트 길이 기반 기본 강도
        base_intensity = min(len(text) / 100, 1.0)
        
        # 감정 키워드 밀도
        emotion_str = primary_emotion.value.lower()
        if emotion_str in self.emotion_keywords:
            keyword_count = sum(
                text.lower().count(keyword) 
                for keyword in self.emotion_keywords[emotion_str]
            )
            keyword_intensity = min(keyword_count * 0.2, 1.0)
        else:
            keyword_intensity = 0.5
        
        # 강조 표현 확인
        emphasis_patterns = ['!', '?', '...', '정말', '너무', '아주', '매우', '완전', '진짜']
        emphasis_count = sum(text.count(pattern) for pattern in emphasis_patterns)
        emphasis_intensity = min(emphasis_count * 0.1, 0.5)
        
        # 최종 강도 계산
        final_intensity = (base_intensity + keyword_intensity + emphasis_intensity) / 3
        
        return round(min(max(final_intensity, 0.1), 1.0), 2)
    
    def _calculate_confidence(self, emotion_scores: Dict[str, float]) -> float:
        """분석 신뢰도 계산"""
        if not emotion_scores:
            return 0.0
        
        # 최고 점수와 두 번째 점수의 차이
        sorted_scores = sorted(emotion_scores.values(), reverse=True)
        
        if len(sorted_scores) == 1:
            return sorted_scores[0]
        
        score_diff = sorted_scores[0] - sorted_scores[1]
        confidence = sorted_scores[0] * (1 + score_diff)
        
        return round(min(confidence, 1.0), 2)
    
    def _extract_emotion_keywords(self, text: str, primary_emotion: EmotionTypeEnum) -> List[str]:
        """감정 키워드 추출"""
        emotion_str = primary_emotion.value.lower()
        if emotion_str not in self.emotion_keywords:
            return []
        
        found_keywords = []
        text_lower = text.lower()
        
        for keyword in self.emotion_keywords[emotion_str]:
            if keyword in text_lower:
                found_keywords.append(keyword)
        
        return found_keywords
    
    async def analyze_emotion_trend(
        self,
        user_id: str,
        emotions_data: List[Dict[str, Any]],
        days_back: int = 30
    ) -> EmotionTrendAnalysis:
        """
        감정 트렌드 분석
        
        Args:
            user_id: 사용자 ID
            emotions_data: 감정 데이터 리스트
            days_back: 분석할 과거 일수
            
        Returns:
            EmotionTrendAnalysis: 트렌드 분석 결과
        """
        try:
            # 날짜 범위 설정
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days_back)
            
            # 기간 내 데이터 필터링
            filtered_data = [
                data for data in emotions_data
                if start_date <= data.get('timestamp', datetime.now()) <= end_date
            ]
            
            if not filtered_data:
                return EmotionTrendAnalysis(
                    user_id=user_id,
                    period_start=start_date,
                    period_end=end_date,
                    dominant_emotion=EmotionTypeEnum.CALM,
                    emotion_distribution={},
                    trend_direction="stable",
                    average_intensity=0.5,
                    total_entries=0,
                    insights=["분석할 데이터가 부족합니다."]
                )
            
            # 감정 분포 계산
            emotion_counts = {}
            total_intensity = 0
            
            for data in filtered_data:
                emotion = data.get('emotion', 'calm')
                emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1
                total_intensity += data.get('intensity', 0.5)
            
            # 감정 분포 정규화
            total_count = len(filtered_data)
            emotion_distribution = {
                emotion: count / total_count 
                for emotion, count in emotion_counts.items()
            }
            
            # 지배적 감정
            dominant_emotion_str = max(emotion_counts.keys(), key=lambda k: emotion_counts[k])
            dominant_emotion = EmotionTypeEnum(dominant_emotion_str)
            
            # 트렌드 방향 분석
            trend_direction = self._analyze_trend_direction(filtered_data)
            
            # 평균 강도
            average_intensity = total_intensity / total_count
            
            # 인사이트 생성
            insights = await self._generate_emotion_insights(
                emotion_distribution, dominant_emotion, trend_direction, average_intensity
            )
            
            return EmotionTrendAnalysis(
                user_id=user_id,
                period_start=start_date,
                period_end=end_date,
                dominant_emotion=dominant_emotion,
                emotion_distribution=emotion_distribution,
                trend_direction=trend_direction,
                average_intensity=round(average_intensity, 2),
                total_entries=total_count,
                insights=insights
            )
            
        except Exception as e:
            logger.error(f"감정 트렌드 분석 실패: {str(e)}")
            return EmotionTrendAnalysis(
                user_id=user_id,
                period_start=start_date,
                period_end=end_date,
                dominant_emotion=EmotionTypeEnum.CALM,
                emotion_distribution={},
                trend_direction="unknown",
                average_intensity=0.5,
                total_entries=0,
                insights=["트렌드 분석 중 오류가 발생했습니다."]
            )
    
    def _analyze_trend_direction(self, emotions_data: List[Dict[str, Any]]) -> str:
        """트렌드 방향 분석"""
        if len(emotions_data) < 3:
            return "stable"
        
        # 시간순 정렬
        sorted_data = sorted(emotions_data, key=lambda x: x.get('timestamp', datetime.now()))
        
        # 긍정적 감정 점수 계산
        positive_emotions = ["happy", "excited", "grateful", "content"]
        
        scores = []
        for data in sorted_data:
            emotion = data.get('emotion', 'calm')
            intensity = data.get('intensity', 0.5)
            
            if emotion in positive_emotions:
                scores.append(intensity)
            elif emotion == 'calm':
                scores.append(0.5)
            else:
                scores.append(1.0 - intensity)  # 부정적 감정은 역산
        
        # 전반부와 후반부 비교
        mid_point = len(scores) // 2
        first_half_avg = sum(scores[:mid_point]) / mid_point if mid_point > 0 else 0.5
        second_half_avg = sum(scores[mid_point:]) / (len(scores) - mid_point)
        
        diff = second_half_avg - first_half_avg
        
        if diff > 0.1:
            return "improving"
        elif diff < -0.1:
            return "declining"
        else:
            return "stable"
    
    async def _generate_emotion_insights(
        self,
        emotion_distribution: Dict[str, float],
        dominant_emotion: EmotionTypeEnum,
        trend_direction: str,
        average_intensity: float
    ) -> List[str]:
        """감정 인사이트 생성"""
        insights = []
        
        # 지배적 감정 인사이트
        if dominant_emotion == EmotionTypeEnum.HAPPY:
            insights.append("전반적으로 긍정적인 감정 상태를 유지하고 있습니다.")
        elif dominant_emotion == EmotionTypeEnum.SAD:
            insights.append("우울한 감정이 자주 나타나고 있어 관심이 필요합니다.")
        elif dominant_emotion == EmotionTypeEnum.LONELY:
            insights.append("외로움을 자주 느끼고 있어 사회적 연결이 필요할 수 있습니다.")
        elif dominant_emotion == EmotionTypeEnum.ANXIOUS:
            insights.append("불안감이 주로 나타나고 있어 안정감을 주는 대화가 도움이 될 것입니다.")
        
        # 트렌드 인사이트
        if trend_direction == "improving":
            insights.append("감정 상태가 점차 개선되고 있는 긍정적인 추세입니다.")
        elif trend_direction == "declining":
            insights.append("감정 상태가 다소 악화되고 있어 더 많은 지원이 필요합니다.")
        else:
            insights.append("감정 상태가 안정적으로 유지되고 있습니다.")
        
        # 강도 인사이트
        if average_intensity > 0.7:
            insights.append("감정 표현이 강하게 나타나고 있습니다.")
        elif average_intensity < 0.3:
            insights.append("감정 표현이 다소 약하게 나타나고 있습니다.")
        
        # 감정 다양성 인사이트
        if len(emotion_distribution) > 5:
            insights.append("다양한 감정을 경험하고 있어 풍부한 감정 생활을 하고 있습니다.")
        elif len(emotion_distribution) <= 2:
            insights.append("감정 표현이 제한적일 수 있어 다양한 활동을 권장합니다.")
        
        return insights
    
    async def detect_emotion_pattern(
        self,
        user_id: str,
        emotions_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        감정 패턴 감지
        
        Args:
            user_id: 사용자 ID
            emotions_data: 감정 데이터
            
        Returns:
            Dict[str, Any]: 패턴 분석 결과
        """
        try:
            # 시간대별 감정 패턴
            time_patterns = self._analyze_time_patterns(emotions_data)
            
            # 감정 전환 패턴
            transition_patterns = self._analyze_transition_patterns(emotions_data)
            
            # 주기적 패턴
            cyclical_patterns = self._analyze_cyclical_patterns(emotions_data)
            
            # 이상 패턴 감지
            anomalies = self._detect_anomalies(emotions_data)
            
            return {
                "user_id": user_id,
                "time_patterns": time_patterns,
                "transition_patterns": transition_patterns,
                "cyclical_patterns": cyclical_patterns,
                "anomalies": anomalies,
                "analysis_date": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"감정 패턴 감지 실패: {str(e)}")
            return {"error": str(e)}
    
    def _analyze_time_patterns(self, emotions_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """시간대별 감정 패턴 분석"""
        hour_emotions = {}
        
        for data in emotions_data:
            timestamp = data.get('timestamp', datetime.now())
            hour = timestamp.hour
            emotion = data.get('emotion', 'calm')
            
            if hour not in hour_emotions:
                hour_emotions[hour] = []
            hour_emotions[hour].append(emotion)
        
        # 시간대별 주요 감정
        hour_patterns = {}
        for hour, emotions in hour_emotions.items():
            if emotions:
                most_common = max(set(emotions), key=emotions.count)
                hour_patterns[hour] = {
                    "dominant_emotion": most_common,
                    "count": len(emotions)
                }
        
        return hour_patterns
    
    def _analyze_transition_patterns(self, emotions_data: List[Dict[str, Any]]) -> Dict[str, int]:
        """감정 전환 패턴 분석"""
        transitions = {}
        
        sorted_data = sorted(emotions_data, key=lambda x: x.get('timestamp', datetime.now()))
        
        for i in range(1, len(sorted_data)):
            prev_emotion = sorted_data[i-1].get('emotion', 'calm')
            curr_emotion = sorted_data[i].get('emotion', 'calm')
            
            if prev_emotion != curr_emotion:
                transition = f"{prev_emotion} -> {curr_emotion}"
                transitions[transition] = transitions.get(transition, 0) + 1
        
        return transitions
    
    def _analyze_cyclical_patterns(self, emotions_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """주기적 패턴 분석"""
        # 요일별 패턴
        weekday_emotions = {}
        
        for data in emotions_data:
            timestamp = data.get('timestamp', datetime.now())
            weekday = timestamp.weekday()  # 0: 월요일, 6: 일요일
            emotion = data.get('emotion', 'calm')
            
            if weekday not in weekday_emotions:
                weekday_emotions[weekday] = []
            weekday_emotions[weekday].append(emotion)
        
        weekday_patterns = {}
        weekday_names = ['월', '화', '수', '목', '금', '토', '일']
        
        for weekday, emotions in weekday_emotions.items():
            if emotions:
                most_common = max(set(emotions), key=emotions.count)
                weekday_patterns[weekday_names[weekday]] = {
                    "dominant_emotion": most_common,
                    "count": len(emotions)
                }
        
        return {"weekday_patterns": weekday_patterns}
    
    def _detect_anomalies(self, emotions_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """이상 패턴 감지"""
        anomalies = []
        
        if len(emotions_data) < 10:
            return anomalies
        
        # 감정 분포 계산
        emotion_counts = {}
        for data in emotions_data:
            emotion = data.get('emotion', 'calm')
            emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1
        
        total_count = len(emotions_data)
        
        # 특정 감정이 과도하게 많은 경우
        for emotion, count in emotion_counts.items():
            ratio = count / total_count
            if ratio > 0.7 and emotion in ['sad', 'angry', 'anxious', 'lonely']:
                anomalies.append({
                    "type": "excessive_negative_emotion",
                    "emotion": emotion,
                    "ratio": ratio,
                    "description": f"{emotion} 감정이 전체의 {ratio:.1%}를 차지합니다."
                })
        
        # 강도가 지속적으로 높은 경우
        high_intensity_count = sum(
            1 for data in emotions_data 
            if data.get('intensity', 0.5) > 0.8
        )
        
        if high_intensity_count / total_count > 0.6:
            anomalies.append({
                "type": "high_intensity_pattern",
                "ratio": high_intensity_count / total_count,
                "description": "감정 강도가 지속적으로 높게 나타납니다."
            })
        
        return anomalies
    
    async def health_check(self) -> Dict[str, Any]:
        """
        감정 서비스 상태 확인
        
        Returns:
            Dict[str, Any]: 상태 정보
        """
        try:
            # 테스트 감정 분석
            test_result = await self.analyze_emotion("테스트 메시지입니다.", use_ai=False)
            
            return {
                "status": "healthy",
                "model": "gemini-2.0-flash-exp",
                "emotion_keywords_count": sum(len(keywords) for keywords in self.emotion_keywords.values()),
                "test_analysis": {
                    "primary_emotion": test_result.primary_emotion.value,
                    "confidence": test_result.confidence
                }
            }
            
        except Exception as e:
            logger.error(f"감정 서비스 상태 확인 실패: {str(e)}")
            return {
                "status": "unhealthy",
                "error": str(e)
            }

# 전역 감정 서비스 인스턴스
emotion_service = EmotionService()

# 편의 함수들
async def analyze_text_emotion(text: str, user_id: Optional[str] = None) -> EmotionAnalysisResult:
    """텍스트 감정 분석"""
    return await emotion_service.analyze_emotion(text, user_id)

async def get_emotion_trend(
    user_id: str, 
    emotions_data: List[Dict[str, Any]], 
    days_back: int = 30
) -> EmotionTrendAnalysis:
    """감정 트렌드 분석"""
    return await emotion_service.analyze_emotion_trend(user_id, emotions_data, days_back)

async def detect_emotion_patterns(
    user_id: str, 
    emotions_data: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """감정 패턴 감지"""
    return await emotion_service.detect_emotion_pattern(user_id, emotions_data) 