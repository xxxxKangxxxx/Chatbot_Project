"""
일정 관리 Pydantic 스키마

사용자의 다양한 일정(약물 복용, 병원 예약, 운동, 취미 활동 등)을 관리하는 스키마입니다.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, date, time
from enum import Enum
from pydantic import BaseModel, Field, validator, field_validator, model_validator

# 일정 유형 열거형
class ScheduleType(str, Enum):
    MEDICATION = "medication"           # 약물 복용
    MEDICAL_APPOINTMENT = "medical"     # 병원 예약
    EXERCISE = "exercise"               # 운동
    HOBBY = "hobby"                     # 취미 활동
    FAMILY = "family"                   # 가족 모임
    SOCIAL = "social"                   # 사회 활동
    PERSONAL = "personal"               # 개인 일정
    REMINDER = "reminder"               # 일반 알림
    OTHER = "other"                     # 기타

# 일정 상태 열거형
class ScheduleStatus(str, Enum):
    ACTIVE = "active"                   # 활성
    COMPLETED = "completed"             # 완료
    CANCELLED = "cancelled"             # 취소
    POSTPONED = "postponed"             # 연기
    INACTIVE = "inactive"               # 비활성

# 반복 유형 열거형
class RecurrenceType(str, Enum):
    NONE = "none"                       # 반복 없음
    DAILY = "daily"                     # 매일
    WEEKLY = "weekly"                   # 매주
    MONTHLY = "monthly"                 # 매월
    YEARLY = "yearly"                   # 매년
    CUSTOM = "custom"                   # 사용자 정의

# 우선순위 열거형
class Priority(str, Enum):
    LOW = "low"                         # 낮음
    MEDIUM = "medium"                   # 보통
    HIGH = "high"                       # 높음
    URGENT = "urgent"                   # 긴급

# 알림 기록 상태
class LogStatus(str, Enum):
    COMPLETED = "completed"             # 완료
    MISSED = "missed"                   # 놓침
    POSTPONED = "postponed"             # 연기
    CANCELLED = "cancelled"             # 취소

# === 일정 스키마 ===

class ScheduleBase(BaseModel):
    """일정 기본 스키마"""
    title: str = Field(..., min_length=1, max_length=200, description="일정 제목")
    schedule_type: ScheduleType = Field(..., description="일정 유형")
    description: Optional[str] = Field(None, max_length=1000, description="일정 설명")
    location: Optional[str] = Field(None, max_length=200, description="장소")
    priority: Priority = Field(Priority.MEDIUM, description="우선순위")
    is_all_day: bool = Field(False, description="종일 일정 여부")
    
    # 반복 설정
    recurrence_type: RecurrenceType = Field(RecurrenceType.NONE, description="반복 유형")
    recurrence_interval: Optional[int] = Field(None, ge=1, description="반복 간격")
    recurrence_days: Optional[List[int]] = Field(None, description="반복 요일 (0=월요일)")
    recurrence_end_date: Optional[date] = Field(None, description="반복 종료 날짜")
    
    # 알림 설정
    reminder_minutes: List[int] = Field(default=[15], description="알림 시간 (분 단위)")
    
    # 추가 정보 (약물의 경우 복용량, 운동의 경우 운동 종류 등)
    metadata: Optional[Dict[str, Any]] = Field(default={}, description="추가 메타데이터")
    
    notes: Optional[str] = Field(None, max_length=500, description="메모")

class ScheduleCreate(ScheduleBase):
    """일정 생성 스키마"""
    user_id: str = Field(..., description="사용자 ID")
    start_datetime: datetime = Field(..., description="시작 날짜/시간")
    end_datetime: Optional[datetime] = Field(None, description="종료 날짜/시간")
    
    @validator('end_datetime')
    def validate_end_datetime(cls, v, values):
        if v and 'start_datetime' in values and v <= values['start_datetime']:
            raise ValueError('종료 시간은 시작 시간보다 뒤여야 합니다')
        return v

class ScheduleUpdate(BaseModel):
    """일정 수정 스키마"""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    schedule_type: Optional[ScheduleType] = None
    description: Optional[str] = Field(None, max_length=1000)
    location: Optional[str] = Field(None, max_length=200)
    priority: Optional[Priority] = None
    start_datetime: Optional[datetime] = None
    end_datetime: Optional[datetime] = None
    is_all_day: Optional[bool] = None
    status: Optional[ScheduleStatus] = None
    
    recurrence_type: Optional[RecurrenceType] = None
    recurrence_interval: Optional[int] = Field(None, ge=1)
    recurrence_days: Optional[List[int]] = None
    recurrence_end_date: Optional[date] = None
    
    reminder_minutes: Optional[List[int]] = None
    metadata: Optional[Dict[str, Any]] = None
    notes: Optional[str] = Field(None, max_length=500)

class ScheduleResponse(ScheduleBase):
    """일정 응답 스키마"""
    id: str
    user_id: str
    start_datetime: datetime
    end_datetime: Optional[datetime]
    status: ScheduleStatus
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# === 일정 기록 스키마 ===

class ScheduleLogBase(BaseModel):
    """일정 기록 기본 스키마"""
    status: LogStatus = Field(..., description="완료 상태")
    completed_at: Optional[datetime] = Field(None, description="완료 시간")
    notes: Optional[str] = Field(None, max_length=500, description="메모")

class ScheduleLogCreate(ScheduleLogBase):
    """일정 기록 생성 스키마"""
    user_id: str = Field(..., description="사용자 ID")
    schedule_id: str = Field(..., description="일정 ID")
    scheduled_datetime: datetime = Field(..., description="예정된 날짜/시간")

class ScheduleLogUpdate(BaseModel):
    """일정 기록 수정 스키마"""
    status: Optional[LogStatus] = None
    completed_at: Optional[datetime] = None
    notes: Optional[str] = Field(None, max_length=500)

class ScheduleLogResponse(ScheduleLogBase):
    """일정 기록 응답 스키마"""
    id: str
    user_id: str
    schedule_id: str
    scheduled_datetime: datetime
    created_at: datetime
    
    class Config:
        from_attributes = True

# === 알림 스키마 ===

class ReminderResponse(BaseModel):
    """알림 응답 스키마"""
    schedule_id: str
    title: str
    schedule_type: ScheduleType
    description: Optional[str]
    location: Optional[str]
    priority: Priority
    scheduled_datetime: datetime
    reminder_datetime: datetime
    status: str = "pending"
    is_overdue: bool = False
    time_until_due: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = {}

# === 통계 스키마 ===

class ScheduleStatsResponse(BaseModel):
    """일정 통계 응답 스키마"""
    user_id: str
    period_days: int
    total_scheduled: int
    total_completed: int
    total_missed: int
    completion_rate: float
    on_time_rate: float
    type_breakdown: Dict[str, int]
    priority_breakdown: Dict[str, int]
    daily_completion: Dict[str, int]
    missed_by_time: Dict[str, int]
    current_streak_days: int

class ComplianceResponse(BaseModel):
    """순응도 분석 응답 스키마"""
    user_id: str
    analysis_period_days: int
    overall_completion_rate: float
    type_compliance: Dict[str, float]
    time_compliance: Dict[str, float]
    missed_patterns: Dict[str, Any]
    compliance_trend: str  # improving, declining, stable
    recommendations: List[str]
    risk_level: str  # low, medium, high
    last_updated: datetime

# === 캘린더 스키마 ===

class CalendarDayResponse(BaseModel):
    """캘린더 일별 응답 스키마"""
    date: date
    total_schedules: int
    completed_schedules: int
    pending_schedules: int
    overdue_schedules: int
    schedules: List[ScheduleResponse]

class CalendarWeekResponse(BaseModel):
    """캘린더 주별 응답 스키마"""
    week_start: date
    week_end: date
    days: List[CalendarDayResponse]
    week_summary: Dict[str, int]

class CalendarMonthResponse(BaseModel):
    """캘린더 월별 응답 스키마"""
    year: int
    month: int
    weeks: List[CalendarWeekResponse]
    month_summary: Dict[str, int]

# === 검색 및 필터 스키마 ===

class ScheduleSearchRequest(BaseModel):
    """일정 검색 요청 스키마"""
    query: Optional[str] = Field(None, description="검색어")
    schedule_types: Optional[List[ScheduleType]] = Field(None, description="일정 유형 필터")
    priority: Optional[Priority] = Field(None, description="우선순위 필터")
    status: Optional[ScheduleStatus] = Field(None, description="상태 필터")
    start_date: Optional[date] = Field(None, description="시작 날짜")
    end_date: Optional[date] = Field(None, description="종료 날짜")
    location: Optional[str] = Field(None, description="장소")

class ScheduleListResponse(BaseModel):
    """일정 목록 응답 스키마"""
    schedules: List[ScheduleResponse]
    total_count: int
    filtered_count: int
    page: int
    limit: int
    has_more: bool

# === 일괄 처리 스키마 ===

class ScheduleBatchRequest(BaseModel):
    """일정 일괄 처리 요청 스키마"""
    schedule_ids: List[str] = Field(..., description="일정 ID 목록")
    action: str = Field(..., description="수행할 액션 (complete, cancel, postpone)")
    action_data: Optional[Dict[str, Any]] = Field(default={}, description="액션 추가 데이터")

class ScheduleBatchResponse(BaseModel):
    """일정 일괄 처리 응답 스키마"""
    success_count: int
    failed_count: int
    total_count: int
    success_ids: List[str]
    failed_ids: List[str]
    errors: List[str]

# === 템플릿 스키마 ===

class ScheduleTemplateCreate(BaseModel):
    """일정 템플릿 생성 스키마"""
    user_id: str
    name: str = Field(..., min_length=1, max_length=100, description="템플릿 이름")
    description: Optional[str] = Field(None, max_length=500)
    schedule_type: ScheduleType
    default_duration_minutes: Optional[int] = Field(None, ge=1)
    default_reminder_minutes: List[int] = Field(default=[15])
    default_priority: Priority = Priority.MEDIUM
    template_data: Dict[str, Any] = Field(default={}, description="템플릿 데이터")

class ScheduleTemplateResponse(BaseModel):
    """일정 템플릿 응답 스키마"""
    id: str
    user_id: str
    name: str
    description: Optional[str]
    schedule_type: ScheduleType
    default_duration_minutes: Optional[int]
    default_reminder_minutes: List[int]
    default_priority: Priority
    template_data: Dict[str, Any]
    usage_count: int = 0
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# === 인사이트 스키마 ===

class ScheduleInsightResponse(BaseModel):
    """일정 인사이트 응답 스키마"""
    user_id: str
    analysis_period: int
    insights: List[str]
    productivity_score: float
    schedule_balance: Dict[str, float]  # 일정 유형별 비율
    peak_productivity_hours: List[int]
    improvement_suggestions: List[str]
    habit_analysis: Dict[str, Any]
    generated_at: datetime 