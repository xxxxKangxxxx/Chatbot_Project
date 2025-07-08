"""
일정 관리 SQLAlchemy 모델

사용자의 다양한 일정(약물 복용, 병원 예약, 운동, 취미 활동 등)을 관리하는 데이터베이스 모델입니다.
"""

from sqlalchemy import Column, String, DateTime, Boolean, Integer, Text, JSON, Date, Time, Float
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from sqlalchemy import ForeignKey
from app.database import Base


class Schedule(Base):
    """
    일정 모델
    
    사용자의 다양한 일정을 관리합니다.
    약물 복용, 병원 예약, 운동, 취미 활동 등 모든 종류의 일정을 포함합니다.
    """
    __tablename__ = "schedules"

    id = Column(String(36), primary_key=True, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # 기본 일정 정보
    title = Column(String(200), nullable=False, comment="일정 제목")
    schedule_type = Column(String(50), nullable=False, index=True, comment="일정 유형")
    description = Column(Text, nullable=True, comment="일정 설명")
    location = Column(String(200), nullable=True, comment="장소")
    priority = Column(String(20), nullable=False, default="medium", comment="우선순위")
    
    # 시간 정보
    start_datetime = Column(DateTime, nullable=False, index=True, comment="시작 날짜/시간")
    end_datetime = Column(DateTime, nullable=True, comment="종료 날짜/시간")
    is_all_day = Column(Boolean, default=False, comment="종일 일정 여부")
    
    # 반복 설정
    recurrence_type = Column(String(20), default="none", comment="반복 유형")
    recurrence_interval = Column(Integer, nullable=True, comment="반복 간격")
    recurrence_days = Column(JSON, nullable=True, comment="반복 요일")
    recurrence_end_date = Column(Date, nullable=True, comment="반복 종료 날짜")
    
    # 알림 설정
    reminder_minutes = Column(JSON, default=lambda: [15], comment="알림 시간 (분 단위)")
    
    # 상태 및 메타데이터
    status = Column(String(20), nullable=False, default="active", index=True, comment="일정 상태")
    additional_data = Column(JSON, default=dict, comment="추가 메타데이터")
    notes = Column(Text, nullable=True, comment="메모")
    
    # 타임스탬프
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    # 관계 설정
    user = relationship("User", back_populates="schedules")
    schedule_logs = relationship("ScheduleLog", back_populates="schedule", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Schedule(id='{self.id}', title='{self.title}', type='{self.schedule_type}', user_id='{self.user_id}')>"


class ScheduleLog(Base):
    """
    일정 기록 모델
    
    사용자의 일정 완료, 미완료, 연기 등의 기록을 관리합니다.
    """
    __tablename__ = "schedule_logs"

    id = Column(String(36), primary_key=True, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    schedule_id = Column(String(36), ForeignKey("schedules.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # 기록 정보
    scheduled_datetime = Column(DateTime, nullable=False, comment="예정된 날짜/시간")
    completed_at = Column(DateTime, nullable=True, comment="완료 시간")
    status = Column(String(20), nullable=False, comment="완료 상태")  # completed, missed, postponed, cancelled
    notes = Column(Text, nullable=True, comment="메모")
    
    # 타임스탬프
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    # 관계 설정
    user = relationship("User", back_populates="schedule_logs")
    schedule = relationship("Schedule", back_populates="schedule_logs")

    def __repr__(self):
        return f"<ScheduleLog(id='{self.id}', schedule_id='{self.schedule_id}', status='{self.status}')>"


class ScheduleTemplate(Base):
    """
    일정 템플릿 모델
    
    자주 사용하는 일정 패턴을 템플릿으로 저장하여 재사용할 수 있습니다.
    """
    __tablename__ = "schedule_templates"

    id = Column(String(36), primary_key=True, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # 템플릿 정보
    name = Column(String(100), nullable=False, comment="템플릿 이름")
    description = Column(Text, nullable=True, comment="템플릿 설명")
    schedule_type = Column(String(50), nullable=False, comment="일정 유형")
    
    # 기본 설정
    default_duration_minutes = Column(Integer, nullable=True, comment="기본 소요 시간 (분)")
    default_reminder_minutes = Column(JSON, default=lambda: [15], comment="기본 알림 시간")
    default_priority = Column(String(20), default="medium", comment="기본 우선순위")
    
    # 템플릿 데이터
    template_data = Column(JSON, default=dict, comment="템플릿 데이터")
    
    # 사용 통계
    usage_count = Column(Integer, default=0, comment="사용 횟수")
    
    # 타임스탬프
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    # 관계 설정
    user = relationship("User", back_populates="schedule_templates")

    def __repr__(self):
        return f"<ScheduleTemplate(id='{self.id}', name='{self.name}', type='{self.schedule_type}')>"


class Reminder(Base):
    """
    알림 모델
    
    일정에 대한 알림을 관리합니다.
    """
    __tablename__ = "reminders"

    id = Column(String(36), primary_key=True, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    schedule_id = Column(String(36), ForeignKey("schedules.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # 알림 정보
    reminder_datetime = Column(DateTime, nullable=False, index=True, comment="알림 시간")
    message = Column(Text, nullable=True, comment="알림 메시지")
    reminder_type = Column(String(20), default="notification", comment="알림 유형")
    
    # 상태
    is_sent = Column(Boolean, default=False, comment="발송 여부")
    sent_at = Column(DateTime, nullable=True, comment="발송 시간")
    is_acknowledged = Column(Boolean, default=False, comment="확인 여부")
    acknowledged_at = Column(DateTime, nullable=True, comment="확인 시간")
    
    # 스누즈 기능
    snooze_count = Column(Integer, default=0, comment="스누즈 횟수")
    snooze_until = Column(DateTime, nullable=True, comment="스누즈 종료 시간")
    
    # 타임스탬프
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    # 관계 설정
    user = relationship("User", back_populates="reminders")
    schedule = relationship("Schedule")

    def __repr__(self):
        return f"<Reminder(id='{self.id}', schedule_id='{self.schedule_id}', reminder_time='{self.reminder_datetime}')>"


class ScheduleStats(Base):
    """
    일정 통계 모델
    
    사용자의 일정 관련 통계를 저장합니다.
    """
    __tablename__ = "schedule_stats"

    id = Column(String(36), primary_key=True, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # 통계 기간
    stat_date = Column(Date, nullable=False, index=True, comment="통계 날짜")
    period_type = Column(String(20), nullable=False, comment="기간 유형")  # daily, weekly, monthly
    
    # 기본 통계
    total_scheduled = Column(Integer, default=0, comment="총 예정 일정")
    total_completed = Column(Integer, default=0, comment="총 완료 일정")
    total_missed = Column(Integer, default=0, comment="총 미완료 일정")
    completion_rate = Column(Float, default=0.0, comment="완료율")
    
    # 유형별 통계
    type_breakdown = Column(JSON, default=dict, comment="유형별 분류")
    priority_breakdown = Column(JSON, default=dict, comment="우선순위별 분류")
    
    # 시간대별 통계
    hourly_completion = Column(JSON, default=dict, comment="시간대별 완료율")
    
    # 추가 메트릭
    average_completion_time = Column(Float, nullable=True, comment="평균 완료 시간 (분)")
    productivity_score = Column(Float, default=0.0, comment="생산성 점수")
    
    # 타임스탬프
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    # 관계 설정
    user = relationship("User", back_populates="schedule_stats")

    def __repr__(self):
        return f"<ScheduleStats(user_id='{self.user_id}', date='{self.stat_date}', completion_rate={self.completion_rate})>" 