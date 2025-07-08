"""
사용자 모델 정의
=====================================================

사용자 정보를 저장하는 SQLAlchemy 모델
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database import Base


class User(Base):
    """사용자 테이블"""
    
    __tablename__ = "users"
    
    # 기본 정보
    id = Column(String(36), primary_key=True, index=True, comment="사용자 ID")
    name = Column(String(50), nullable=False, comment="사용자 이름")
    age = Column(Integer, comment="나이")
    gender = Column(Enum("M", "F", "OTHER"), default="F", comment="성별")
    
    # 개인화 정보
    speech_style = Column(Text, comment="말투 스타일 (JSON 형태 저장 가능)")
    phone = Column(String(20), comment="연락처 (응급시 사용)")
    profile_image = Column(String(255), comment="프로필 이미지 경로")
    
    # 상태 정보
    is_active = Column(Boolean, default=True, comment="활성 상태")
    last_login = Column(DateTime, comment="마지막 로그인 시간")
    
    # 시간 정보
    created_at = Column(DateTime, default=func.now(), comment="생성일시")
    updated_at = Column(
        DateTime, 
        default=func.now(), 
        onupdate=func.now(), 
        comment="수정일시"
    )
    
    # 관계 정의
    chat_logs = relationship("ChatLog", back_populates="user", cascade="all, delete-orphan")
    emotions = relationship("Emotion", back_populates="user", cascade="all, delete-orphan")
    schedules = relationship("Schedule", back_populates="user", cascade="all, delete-orphan")
    schedule_logs = relationship("ScheduleLog", back_populates="user", cascade="all, delete-orphan")
    schedule_templates = relationship("ScheduleTemplate", back_populates="user", cascade="all, delete-orphan")
    schedule_stats = relationship("ScheduleStats", back_populates="user", cascade="all, delete-orphan")
    reminders = relationship("Reminder", back_populates="user", cascade="all, delete-orphan")
    interests = relationship("Interest", back_populates="user", cascade="all, delete-orphan")
    chat_sessions = relationship("ChatSession", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(id={self.id}, name='{self.name}', age={self.age})>"
    
    def to_dict(self):
        """모델을 딕셔너리로 변환"""
        return {
            "id": self.id,
            "name": self.name,
            "age": self.age,
            "gender": self.gender,
            "speech_style": self.speech_style,
            "phone": self.phone,
            "profile_image": self.profile_image,
            "is_active": self.is_active,
            "last_login": self.last_login,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }
    
    @property
    def display_name(self):
        """표시용 이름 (존댓말 포함)"""
        return f"{self.name}님"
    
    @property
    def age_group(self):
        """연령대 분류"""
        if not self.age:
            return "미상"
        elif self.age < 60:
            return "중년"
        elif self.age < 70:
            return "초고령"
        else:
            return "고령"
    
    def update_last_login(self):
        """마지막 로그인 시간 업데이트"""
        self.last_login = datetime.now()
    
    def is_new_user(self, days: int = 7):
        """신규 사용자 여부 확인"""
        if not self.created_at:
            return False
        
        from datetime import timedelta
        return (datetime.now() - self.created_at) <= timedelta(days=days) 