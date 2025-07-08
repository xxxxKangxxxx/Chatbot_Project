"""
관심사 모델 정의
=====================================================

사용자 관심사를 저장하는 SQLAlchemy 모델
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database import Base


class Interest(Base):
    """사용자 관심사 테이블"""
    
    __tablename__ = "interests"
    
    # 기본 정보
    id = Column(String(36), primary_key=True, index=True, comment="관심사 ID")
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, comment="사용자 ID")
    keyword = Column(String(50), nullable=False, comment="관심사 키워드")
    
    # 분류 정보
    category = Column(String(30), comment="카테고리 (가족, 취미, 건강, 음식 등)")
    
    # 가중치 정보
    weight = Column(Float, default=1.0, comment="관심도 가중치")
    mentioned_count = Column(Integer, default=1, comment="언급 횟수")
    
    # 시간 정보
    last_mentioned = Column(DateTime, default=func.now(), comment="마지막 언급 시간")
    is_active = Column(Boolean, default=True, comment="활성 상태")
    created_at = Column(DateTime, default=func.now(), comment="생성일시")
    
    # 관계 정의
    user = relationship("User", back_populates="interests")
    
    def __repr__(self):
        return f"<Interest(id={self.id}, user_id={self.user_id}, keyword='{self.keyword}')>"
    
    def to_dict(self):
        """모델을 딕셔너리로 변환"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "keyword": self.keyword,
            "category": self.category,
            "weight": self.weight,
            "mentioned_count": self.mentioned_count,
            "last_mentioned": self.last_mentioned,
            "is_active": self.is_active,
            "created_at": self.created_at
        }
    
    @property
    def interest_level(self):
        """관심도 레벨 분류"""
        if self.weight >= 2.0:
            return "매우 높음"
        elif self.weight >= 1.5:
            return "높음"
        elif self.weight >= 1.0:
            return "보통"
        elif self.weight >= 0.5:
            return "낮음"
        else:
            return "매우 낮음"
    
    @property
    def is_recent(self):
        """최근 언급 여부 (7일 이내)"""
        if not self.last_mentioned:
            return False
        
        from datetime import timedelta
        return (datetime.now() - self.last_mentioned) <= timedelta(days=7)
    
    @property
    def is_trending(self):
        """트렌딩 관심사 여부 (최근 자주 언급)"""
        return self.is_recent and self.mentioned_count >= 3
    
    @property
    def category_emoji(self):
        """카테고리별 이모지 반환"""
        category_emojis = {
            "가족": "👨‍👩‍👧‍👦",
            "취미": "🎨",
            "건강": "🏥",
            "음식": "🍽️",
            "운동": "🏃‍♂️",
            "여행": "✈️",
            "문화": "🎭",
            "종교": "⛪",
            "친구": "👥",
            "펜션": "🏠",
            "쇼핑": "🛒",
            "기타": "📝"
        }
        return category_emojis.get(self.category, "📝")
    
    def increment_mention(self):
        """언급 횟수 증가"""
        self.mentioned_count += 1
        self.last_mentioned = datetime.now()
        
        # 언급 횟수에 따른 가중치 자동 조정
        if self.mentioned_count >= 10:
            self.weight = min(3.0, self.weight + 0.1)
        elif self.mentioned_count >= 5:
            self.weight = min(2.5, self.weight + 0.05)
    
    def update_weight(self, new_weight: float):
        """가중치 업데이트 (0.1 ~ 3.0 범위)"""
        self.weight = max(0.1, min(3.0, new_weight))
    
    def deactivate(self):
        """관심사 비활성화"""
        self.is_active = False
    
    def reactivate(self):
        """관심사 재활성화"""
        self.is_active = True
    
    @classmethod
    def get_default_categories(cls):
        """기본 카테고리 목록 반환"""
        return [
            "가족", "취미", "건강", "음식", "운동", 
            "여행", "문화", "종교", "친구", "펜션", 
            "쇼핑", "기타"
        ]
    
    @classmethod
    def get_category_colors(cls):
        """카테고리별 색상 매핑"""
        return {
            "가족": "#FF6B6B",
            "취미": "#4ECDC4",
            "건강": "#45B7D1",
            "음식": "#FFA07A",
            "운동": "#98D8C8",
            "여행": "#F7DC6F",
            "문화": "#BB8FCE",
            "종교": "#85C1E9",
            "친구": "#F8C471",
            "펜션": "#82E0AA",
            "쇼핑": "#F1948A",
            "기타": "#D5DBDB"
        }
    
    def get_category_color(self):
        """해당 카테고리의 색상 반환"""
        colors = self.get_category_colors()
        return colors.get(self.category, "#D5DBDB")


class InterestTrend(Base):
    """관심사 트렌드 테이블 (일별/주별 통계)"""
    
    __tablename__ = "interest_trends"
    
    # 기본 정보
    id = Column(String(36), primary_key=True, index=True, comment="트렌드 ID")
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, comment="사용자 ID")
    
    # 기간 정보
    trend_date = Column(DateTime, nullable=False, comment="트렌드 날짜")
    period_type = Column(String(10), nullable=False, comment="기간 유형 (daily, weekly)")
    
    # 트렌드 정보
    top_interests = Column(String(500), comment="상위 관심사 (JSON)")
    total_mentions = Column(Integer, default=0, comment="총 언급 횟수")
    new_interests = Column(Integer, default=0, comment="새로운 관심사 수")
    
    # 카테고리 분포
    category_distribution = Column(String(1000), comment="카테고리 분포 (JSON)")
    
    created_at = Column(DateTime, default=func.now(), comment="생성일시")
    
    # 관계 정의
    user = relationship("User")
    
    def __repr__(self):
        return f"<InterestTrend(id={self.id}, user_id={self.user_id}, date={self.trend_date})>"
    
    def to_dict(self):
        """모델을 딕셔너리로 변환"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "trend_date": self.trend_date,
            "period_type": self.period_type,
            "top_interests": self.top_interests,
            "total_mentions": self.total_mentions,
            "new_interests": self.new_interests,
            "category_distribution": self.category_distribution,
            "created_at": self.created_at
        }
    
    def get_top_interests_list(self):
        """상위 관심사를 리스트로 반환"""
        if not self.top_interests:
            return []
        
        import json
        try:
            return json.loads(self.top_interests)
        except:
            return []
    
    def set_top_interests(self, interests_list):
        """상위 관심사 리스트를 JSON으로 저장"""
        import json
        self.top_interests = json.dumps(interests_list, ensure_ascii=False)
    
    def get_category_distribution_dict(self):
        """카테고리 분포를 딕셔너리로 반환"""
        if not self.category_distribution:
            return {}
        
        import json
        try:
            return json.loads(self.category_distribution)
        except:
            return {}
    
    def set_category_distribution(self, distribution_dict):
        """카테고리 분포 딕셔너리를 JSON으로 저장"""
        import json
        self.category_distribution = json.dumps(distribution_dict, ensure_ascii=False)


class InterestKeyword(Base):
    """관심사 키워드 사전 테이블"""
    
    __tablename__ = "interest_keywords"
    
    # 기본 정보
    id = Column(String(36), primary_key=True, index=True, comment="키워드 ID")
    keyword = Column(String(100), nullable=False, unique=True, comment="키워드")
    category = Column(String(30), nullable=False, comment="카테고리")
    
    # 키워드 정보
    synonyms = Column(String(500), comment="동의어 (JSON)")
    related_keywords = Column(String(500), comment="관련 키워드 (JSON)")
    
    # 통계 정보
    usage_count = Column(Integer, default=0, comment="사용 횟수")
    confidence_score = Column(Float, default=1.0, comment="신뢰도 점수")
    
    # 상태 정보
    is_active = Column(Boolean, default=True, comment="활성 상태")
    created_at = Column(DateTime, default=func.now(), comment="생성일시")
    
    def __repr__(self):
        return f"<InterestKeyword(id={self.id}, keyword='{self.keyword}', category='{self.category}')>"
    
    def to_dict(self):
        """모델을 딕셔너리로 변환"""
        return {
            "id": self.id,
            "keyword": self.keyword,
            "category": self.category,
            "synonyms": self.synonyms,
            "related_keywords": self.related_keywords,
            "usage_count": self.usage_count,
            "confidence_score": self.confidence_score,
            "is_active": self.is_active,
            "created_at": self.created_at
        }
    
    def get_synonyms_list(self):
        """동의어를 리스트로 반환"""
        if not self.synonyms:
            return []
        
        import json
        try:
            return json.loads(self.synonyms)
        except:
            return []
    
    def set_synonyms(self, synonyms_list):
        """동의어 리스트를 JSON으로 저장"""
        import json
        self.synonyms = json.dumps(synonyms_list, ensure_ascii=False)
    
    def get_related_keywords_list(self):
        """관련 키워드를 리스트로 반환"""
        if not self.related_keywords:
            return []
        
        import json
        try:
            return json.loads(self.related_keywords)
        except:
            return []
    
    def set_related_keywords(self, keywords_list):
        """관련 키워드 리스트를 JSON으로 저장"""
        import json
        self.related_keywords = json.dumps(keywords_list, ensure_ascii=False)
    
    def increment_usage(self):
        """사용 횟수 증가"""
        self.usage_count += 1
    
    def update_confidence(self, new_score: float):
        """신뢰도 점수 업데이트 (0.0 ~ 1.0 범위)"""
        self.confidence_score = max(0.0, min(1.0, new_score))


class InterestLog(Base):
    """관심사 로그 테이블 (관심사 언급 기록)"""
    
    __tablename__ = "interest_logs"
    
    # 기본 정보
    id = Column(String(36), primary_key=True, index=True, comment="로그 ID")
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, comment="사용자 ID")
    interest_id = Column(String(36), ForeignKey("interests.id", ondelete="CASCADE"), comment="관심사 ID")
    
    # 로그 정보
    category = Column(String(30), nullable=False, comment="관심사 카테고리")
    keyword = Column(String(50), nullable=False, comment="감지된 키워드")
    context = Column(String(500), comment="언급 맥락")
    
    # 감지 정보
    detection_method = Column(String(20), default="keyword", comment="감지 방법")
    confidence = Column(Float, default=1.0, comment="신뢰도")
    
    # 시간 정보
    created_at = Column(DateTime, default=func.now(), comment="생성일시")
    
    # 관계 정의
    user = relationship("User")
    interest = relationship("Interest")
    
    def __repr__(self):
        return f"<InterestLog(id={self.id}, user_id={self.user_id}, keyword='{self.keyword}')>"
    
    def to_dict(self):
        """모델을 딕셔너리로 변환"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "interest_id": self.interest_id,
            "category": self.category,
            "keyword": self.keyword,
            "context": self.context,
            "detection_method": self.detection_method,
            "confidence": self.confidence,
            "created_at": self.created_at
        } 