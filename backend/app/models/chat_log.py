"""
채팅 로그 모델 정의
=====================================================

대화 내용을 저장하는 SQLAlchemy 모델
"""

from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database import Base


class ChatLog(Base):
    """대화 로그 테이블"""
    
    __tablename__ = "chat_logs"
    
    # 기본 정보
    id = Column(String(36), primary_key=True, index=True, comment="대화 로그 ID")
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, comment="사용자 ID")
    role = Column(Enum("user", "bot"), nullable=False, comment="발화 주체")
    message = Column(Text, nullable=False, comment="대화 내용")
    
    # 감정 정보
    emotion = Column(String(20), comment="감정 태그 (기쁨, 우울, 화남, 평온 등)")
    emotion_score = Column(Float, default=0.0, comment="감정 점수 (-1.0 ~ 1.0)")
    
    # 메시지 메타데이터
    message_type = Column(
        Enum("text", "button", "medication", "mood"), 
        default="text", 
        comment="메시지 유형"
    )
    session_id = Column(String(100), comment="대화 세션 ID")
    qdrant_vector_id = Column(String(100), comment="Qdrant 벡터 ID (연동용)")
    
    # 시간 정보
    created_at = Column(DateTime, default=func.now(), comment="생성일시")
    
    # 관계 정의
    user = relationship("User", back_populates="chat_logs")
    
    def __repr__(self):
        return f"<ChatLog(id={self.id}, user_id={self.user_id}, role='{self.role}')>"
    
    def to_dict(self):
        """모델을 딕셔너리로 변환"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "role": self.role,
            "message": self.message,
            "emotion": self.emotion,
            "emotion_score": self.emotion_score,
            "message_type": self.message_type,
            "session_id": self.session_id,
            "qdrant_vector_id": self.qdrant_vector_id,
            "created_at": self.created_at
        }
    
    @property
    def is_user_message(self):
        """사용자 메시지 여부"""
        return self.role == "user"
    
    @property
    def is_bot_message(self):
        """봇 메시지 여부"""
        return self.role == "bot"
    
    @property
    def message_preview(self):
        """메시지 미리보기 (50자 제한)"""
        if len(self.message) <= 50:
            return self.message
        return self.message[:47] + "..."
    
    @property
    def emotion_status(self):
        """감정 상태 분류"""
        if not self.emotion_score:
            return "중립"
        elif self.emotion_score > 0.3:
            return "긍정"
        elif self.emotion_score < -0.3:
            return "부정"
        else:
            return "중립"
    
    def has_vector(self):
        """벡터 저장 여부 확인"""
        return self.qdrant_vector_id is not None
    
    def update_vector_id(self, vector_id: str):
        """벡터 ID 업데이트"""
        self.qdrant_vector_id = vector_id


class ChatSession(Base):
    """대화 세션 테이블"""
    
    __tablename__ = "chat_sessions"
    
    # 기본 정보
    id = Column(String(36), primary_key=True, index=True, comment="세션 ID")
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, comment="사용자 ID")
    session_id = Column(String(100), nullable=False, unique=True, comment="세션 ID")
    
    # 세션 정보
    start_time = Column(DateTime, default=func.now(), comment="세션 시작 시간")
    end_time = Column(DateTime, comment="세션 종료 시간")
    message_count = Column(Integer, default=0, comment="메시지 수")
    avg_emotion_score = Column(Float, comment="평균 감정 점수")
    session_summary = Column(Text, comment="세션 요약")
    
    # 관계 정의
    user = relationship("User", back_populates="chat_sessions")
    
    def __repr__(self):
        return f"<ChatSession(id={self.id}, user_id={self.user_id}, session_id='{self.session_id}')>"
    
    def to_dict(self):
        """모델을 딕셔너리로 변환"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "message_count": self.message_count,
            "avg_emotion_score": self.avg_emotion_score,
            "session_summary": self.session_summary
        }
    
    @property
    def duration(self):
        """세션 지속 시간 (분)"""
        if not self.end_time:
            return None
        
        delta = self.end_time - self.start_time
        return delta.total_seconds() / 60
    
    @property
    def is_active(self):
        """활성 세션 여부"""
        return self.end_time is None
    
    def end_session(self):
        """세션 종료"""
        self.end_time = datetime.now()
    
    def update_message_count(self, count: int):
        """메시지 수 업데이트"""
        self.message_count = count
    
    def update_avg_emotion(self, avg_score: float):
        """평균 감정 점수 업데이트"""
        self.avg_emotion_score = avg_score 