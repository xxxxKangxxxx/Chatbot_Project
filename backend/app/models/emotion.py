"""
감정 모델 정의
=====================================================

감정 분석 결과를 저장하는 SQLAlchemy 모델
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from datetime import datetime, timedelta

from app.database import Base


class Emotion(Base):
    """감정 히스토리 테이블"""
    
    __tablename__ = "emotions"
    
    # 기본 정보
    id = Column(String(36), primary_key=True, index=True, comment="감정 ID")
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, comment="사용자 ID")
    emotion = Column(String(20), nullable=False, comment="감정 유형")
    intensity = Column(Float, nullable=False, comment="감정 강도 (0.0 ~ 1.0)")
    
    # 감정 맥락
    context = Column(Text, comment="감정 발생 맥락")
    trigger_message_id = Column(
        String(36), 
        ForeignKey("chat_logs.id", ondelete="SET NULL"), 
        comment="감정을 유발한 메시지 ID"
    )
    
    # 감지 정보
    detected_method = Column(
        Enum("rule_based", "ml_model", "manual"), 
        default="rule_based", 
        comment="감정 감지 방법"
    )
    detected_at = Column(DateTime, default=func.now(), comment="감지일시")
    
    # 관계 정의
    user = relationship("User", back_populates="emotions")
    trigger_message = relationship("ChatLog", foreign_keys=[trigger_message_id])
    
    def __repr__(self):
        return f"<Emotion(id={self.id}, user_id={self.user_id}, emotion='{self.emotion}', intensity={self.intensity})>"
    
    def to_dict(self):
        """모델을 딕셔너리로 변환"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "emotion": self.emotion,
            "intensity": self.intensity,
            "context": self.context,
            "trigger_message_id": self.trigger_message_id,
            "detected_method": self.detected_method,
            "detected_at": self.detected_at
        }
    
    @property
    def intensity_level(self):
        """감정 강도 레벨 분류"""
        if self.intensity >= 0.8:
            return "매우 강함"
        elif self.intensity >= 0.6:
            return "강함"
        elif self.intensity >= 0.4:
            return "보통"
        elif self.intensity >= 0.2:
            return "약함"
        else:
            return "매우 약함"
    
    @property
    def emotion_category(self):
        """감정 카테고리 분류"""
        positive_emotions = ["기쁨", "행복", "만족", "편안", "희망", "감사"]
        negative_emotions = ["우울", "슬픔", "화남", "불안", "걱정", "외로움"]
        
        if self.emotion in positive_emotions:
            return "긍정"
        elif self.emotion in negative_emotions:
            return "부정"
        else:
            return "중립"
    
    @property
    def is_recent(self):
        """최근 감정 여부 (24시간 이내)"""
        if not self.detected_at:
            return False
        return (datetime.now() - self.detected_at) <= timedelta(hours=24)
    
    @property
    def is_concerning(self):
        """우려되는 감정 여부"""
        concerning_emotions = ["우울", "불안", "외로움", "절망"]
        return self.emotion in concerning_emotions and self.intensity >= 0.6
    
    def get_duration_since_detected(self):
        """감지 후 경과 시간"""
        if not self.detected_at:
            return None
        return datetime.now() - self.detected_at
    
    @classmethod
    def get_emotion_colors(cls):
        """감정별 색상 매핑"""
        return {
            "기쁨": "#FFD700",
            "행복": "#FFA500", 
            "만족": "#32CD32",
            "편안": "#87CEEB",
            "희망": "#98FB98",
            "감사": "#DDA0DD",
            "우울": "#4682B4",
            "슬픔": "#6495ED",
            "화남": "#DC143C",
            "불안": "#FF6347",
            "걱정": "#F4A460",
            "외로움": "#708090",
            "중립": "#D3D3D3"
        }
    
    @classmethod
    def get_emotion_emojis(cls):
        """감정별 이모지 매핑"""
        return {
            "기쁨": "😊",
            "행복": "😄",
            "만족": "😌",
            "편안": "😇",
            "희망": "🌟",
            "감사": "🙏",
            "우울": "😔",
            "슬픔": "😢",
            "화남": "😠",
            "불안": "😰",
            "걱정": "😟",
            "외로움": "😞",
            "중립": "😐"
        }
    
    def get_color(self):
        """해당 감정의 색상 반환"""
        colors = self.get_emotion_colors()
        return colors.get(self.emotion, "#D3D3D3")
    
    def get_emoji(self):
        """해당 감정의 이모지 반환"""
        emojis = self.get_emotion_emojis()
        return emojis.get(self.emotion, "😐")


class EmotionSummary(Base):
    """감정 요약 테이블 (일별/주별 통계)"""
    
    __tablename__ = "emotion_summaries"
    
    # 기본 정보
    id = Column(String(36), primary_key=True, index=True, comment="요약 ID")
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, comment="사용자 ID")
    
    # 기간 정보
    summary_date = Column(DateTime, nullable=False, comment="요약 날짜")
    period_type = Column(Enum("daily", "weekly", "monthly"), nullable=False, comment="기간 유형")
    
    # 감정 통계
    dominant_emotion = Column(String(20), comment="주요 감정")
    avg_intensity = Column(Float, comment="평균 감정 강도")
    emotion_count = Column(Integer, default=0, comment="감정 기록 수")
    
    # 감정 분포 (JSON 형태)
    emotion_distribution = Column(Text, comment="감정 분포 (JSON)")
    
    # 요약 정보
    summary_text = Column(Text, comment="감정 요약 텍스트")
    created_at = Column(DateTime, default=func.now(), comment="생성일시")
    
    # 관계 정의
    user = relationship("User")
    
    def __repr__(self):
        return f"<EmotionSummary(id={self.id}, user_id={self.user_id}, date={self.summary_date})>"
    
    def to_dict(self):
        """모델을 딕셔너리로 변환"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "summary_date": self.summary_date,
            "period_type": self.period_type,
            "dominant_emotion": self.dominant_emotion,
            "avg_intensity": self.avg_intensity,
            "emotion_count": self.emotion_count,
            "emotion_distribution": self.emotion_distribution,
            "summary_text": self.summary_text,
            "created_at": self.created_at
        }
    
    @property
    def period_display(self):
        """기간 표시 형식"""
        if self.period_type == "daily":
            return self.summary_date.strftime("%Y년 %m월 %d일")
        elif self.period_type == "weekly":
            return f"{self.summary_date.strftime('%Y년 %m월 %d일')} 주"
        else:  # monthly
            return self.summary_date.strftime("%Y년 %m월")
    
    def get_emotion_distribution_dict(self):
        """감정 분포를 딕셔너리로 반환"""
        if not self.emotion_distribution:
            return {}
        
        import json
        try:
            return json.loads(self.emotion_distribution)
        except:
            return {}
    
    def set_emotion_distribution(self, distribution_dict):
        """감정 분포 딕셔너리를 JSON으로 저장"""
        import json
        self.emotion_distribution = json.dumps(distribution_dict, ensure_ascii=False) 