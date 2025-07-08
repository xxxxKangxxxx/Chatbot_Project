"""
사용자 관련 Pydantic 스키마
=====================================================

사용자 생성, 업데이트, 응답 모델을 정의합니다.
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
from enum import Enum


class GenderEnum(str, Enum):
    """성별 열거형"""
    MALE = "M"
    FEMALE = "F"
    OTHER = "OTHER"


class UserBase(BaseModel):
    """사용자 기본 스키마"""
    name: str = Field(..., min_length=1, max_length=50, description="사용자 이름")
    age: Optional[int] = Field(None, ge=0, le=120, description="나이")
    gender: Optional[GenderEnum] = Field(GenderEnum.FEMALE, description="성별")
    speech_style: Optional[str] = Field(None, max_length=500, description="말투 스타일")
    phone: Optional[str] = Field(None, max_length=20, description="연락처")


class UserCreate(UserBase):
    """사용자 생성 스키마"""
    
    @validator('phone')
    def validate_phone(cls, v):
        if v and not v.replace('-', '').replace(' ', '').isdigit():
            raise ValueError('유효한 전화번호를 입력해주세요')
        return v
    
    @validator('name')
    def validate_name(cls, v):
        if not v.strip():
            raise ValueError('이름은 필수입니다')
        return v.strip()


class UserUpdate(BaseModel):
    """사용자 업데이트 스키마"""
    name: Optional[str] = Field(None, min_length=1, max_length=50)
    age: Optional[int] = Field(None, ge=0, le=120)
    gender: Optional[GenderEnum] = None
    speech_style: Optional[str] = Field(None, max_length=500)
    phone: Optional[str] = Field(None, max_length=20)
    profile_image: Optional[str] = Field(None, max_length=255)
    is_active: Optional[bool] = None
    
    @validator('phone')
    def validate_phone(cls, v):
        if v and not v.replace('-', '').replace(' ', '').isdigit():
            raise ValueError('유효한 전화번호를 입력해주세요')
        return v


class UserResponse(UserBase):
    """사용자 응답 스키마"""
    id: str = Field(..., description="사용자 ID (UUID)")
    profile_image: Optional[str] = None
    is_active: bool
    last_login: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    # 추가 계산 필드
    display_name: Optional[str] = Field(None, description="표시용 이름")
    age_group: Optional[str] = Field(None, description="연령대")
    
    class Config:
        from_attributes = True
        
    def __init__(self, **data):
        # 계산 필드 설정
        if 'display_name' not in data or not data['display_name']:
            name = data.get('name', '')
            data['display_name'] = f"{name}님" if name else "사용자님"
        
        if 'age_group' not in data or not data['age_group']:
            age = data.get('age')
            if not age:
                data['age_group'] = "미상"
            elif age < 60:
                data['age_group'] = "중년"
            elif age < 70:
                data['age_group'] = "초고령"
            else:
                data['age_group'] = "고령"
        
        super().__init__(**data)


class UserSummary(BaseModel):
    """사용자 요약 정보 스키마"""
    id: str = Field(..., description="사용자 ID (UUID)")
    name: str
    age: Optional[int]
    gender: Optional[GenderEnum]
    is_active: bool
    last_login: Optional[datetime]
    
    class Config:
        from_attributes = True


class UserStats(BaseModel):
    """사용자 통계 스키마"""
    user_id: str = Field(..., description="사용자 ID (UUID)")
    total_messages: int = Field(..., description="총 메시지 수")
    total_sessions: int = Field(..., description="총 세션 수")
    avg_session_duration: Optional[float] = Field(None, description="평균 세션 시간(분)")
    last_active: Optional[datetime] = Field(None, description="마지막 활동 시간")
    
    # 감정 통계
    dominant_emotion: Optional[str] = Field(None, description="주요 감정")
    avg_emotion_score: Optional[float] = Field(None, description="평균 감정 점수")
    
    # 관심사 통계
    top_interests: List[str] = Field(default_factory=list, description="주요 관심사")
    interest_count: int = Field(0, description="관심사 개수")
    
    # 약물 통계
    medication_count: int = Field(0, description="복용 약물 수")
    medication_compliance: Optional[float] = Field(None, description="복용 순응도(%)")


class UserPreferences(BaseModel):
    """사용자 선호도 설정 스키마"""
    user_id: str = Field(..., description="사용자 ID (UUID)")
    speech_style: Optional[str] = Field(None, description="선호하는 말투")
    conversation_style: Optional[str] = Field(None, description="대화 스타일")
    topics_of_interest: List[str] = Field(default_factory=list, description="관심 주제")
    reminder_preferences: dict = Field(default_factory=dict, description="알림 설정")
    privacy_settings: dict = Field(default_factory=dict, description="개인정보 설정")


class UserActivityLog(BaseModel):
    """사용자 활동 로그 스키마"""
    user_id: str = Field(..., description="사용자 ID (UUID)")
    activity_type: str = Field(..., description="활동 유형")
    activity_description: str = Field(..., description="활동 설명")
    timestamp: datetime = Field(..., description="활동 시간")
    metadata: Optional[dict] = Field(None, description="추가 메타데이터")


class UserLogin(BaseModel):
    """사용자 로그인 스키마"""
    user_id: str = Field(..., description="사용자 ID (UUID)")
    login_time: datetime = Field(default_factory=datetime.now)
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


class UserSearchRequest(BaseModel):
    """사용자 검색 요청 스키마"""
    query: Optional[str] = Field(None, min_length=1, description="검색어")
    age_min: Optional[int] = Field(None, ge=0, le=120)
    age_max: Optional[int] = Field(None, ge=0, le=120)
    gender: Optional[GenderEnum] = None
    is_active: Optional[bool] = None
    limit: int = Field(10, ge=1, le=100, description="결과 개수")
    offset: int = Field(0, ge=0, description="시작 위치")
    
    @validator('age_max')
    def validate_age_range(cls, v, values):
        age_min = values.get('age_min')
        if age_min is not None and v is not None and v < age_min:
            raise ValueError('최대 나이는 최소 나이보다 커야 합니다')
        return v


class UserSearchResponse(BaseModel):
    """사용자 검색 응답 스키마"""
    users: List[UserSummary]
    total_count: int
    limit: int
    offset: int
    has_more: bool


class UserProfileUpdate(BaseModel):
    """사용자 프로필 업데이트 스키마"""
    profile_image: Optional[str] = Field(None, description="프로필 이미지 URL")
    speech_style: Optional[str] = Field(None, max_length=500)
    interests: Optional[List[str]] = Field(None, description="관심사 목록")
    emergency_contact: Optional[str] = Field(None, description="응급 연락처")


class UserDashboard(BaseModel):
    """사용자 대시보드 스키마"""
    user: UserResponse
    stats: UserStats
    recent_emotions: List[str] = Field(default_factory=list)
    upcoming_medications: List[dict] = Field(default_factory=list)
    trending_interests: List[str] = Field(default_factory=list)
    health_status: Optional[str] = Field(None, description="건강 상태 요약")


# 응답 메시지 스키마
class UserMessage(BaseModel):
    """사용자 관련 메시지 스키마"""
    message: str
    success: bool = True
    data: Optional[dict] = None


class UserBulkCreate(BaseModel):
    """사용자 일괄 생성 스키마"""
    users: List[UserCreate] = Field(..., min_items=1, max_items=100)


class UserBulkResponse(BaseModel):
    """사용자 일괄 생성 응답 스키마"""
    created_count: int
    failed_count: int
    created_users: List[UserResponse]
    errors: List[str] = Field(default_factory=list)


class UserStatsResponse(BaseModel):
    """사용자 통계 응답 스키마"""
    user_id: str
    total_chat_sessions: int = Field(..., description="총 채팅 세션 수")
    total_messages: int = Field(..., description="총 메시지 수")
    avg_messages_per_session: float = Field(..., description="세션당 평균 메시지 수")
    total_emotions_recorded: int = Field(..., description="기록된 감정 수")
    dominant_emotion: Optional[str] = Field(None, description="주요 감정")
    avg_emotion_intensity: Optional[float] = Field(None, description="평균 감정 강도")
    total_interests: int = Field(..., description="관심사 개수")
    last_activity: Optional[datetime] = Field(None, description="마지막 활동")
    activity_streak_days: int = Field(0, description="연속 활동 일수")
    
    class Config:
        from_attributes = True


class UserListResponse(BaseModel):
    """사용자 목록 응답 스키마"""
    users: List[UserResponse] = Field(..., description="사용자 목록")
    total_count: int = Field(..., description="전체 사용자 수")
    skip: int = Field(..., description="건너뛴 사용자 수")
    limit: int = Field(..., description="조회한 사용자 수")
    has_more: bool = Field(..., description="더 많은 사용자 존재 여부")
    
    class Config:
        from_attributes = True


class PersonalityTraits(BaseModel):
    """성격 특성 스키마"""
    openness: float = Field(0.5, ge=0.0, le=1.0, description="개방성")
    conscientiousness: float = Field(0.5, ge=0.0, le=1.0, description="성실성")
    extraversion: float = Field(0.5, ge=0.0, le=1.0, description="외향성")
    agreeableness: float = Field(0.5, ge=0.0, le=1.0, description="친화성")
    neuroticism: float = Field(0.5, ge=0.0, le=1.0, description="신경성")
    communication_style: str = Field("friendly", description="의사소통 스타일")
    preferred_topics: List[str] = Field(default_factory=list, description="선호 주제")
    response_length: str = Field("medium", description="응답 길이 선호도")
    
    class Config:
        json_schema_extra = {
            "example": {
                "openness": 0.7,
                "conscientiousness": 0.8,
                "extraversion": 0.6,
                "agreeableness": 0.9,
                "neuroticism": 0.3,
                "communication_style": "warm",
                "preferred_topics": ["가족", "건강", "취미"],
                "response_length": "medium"
            }
        } 