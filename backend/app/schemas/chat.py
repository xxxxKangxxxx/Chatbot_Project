"""
채팅 관련 Pydantic 스키마
=====================================================

채팅 요청, 응답, 로그 모델을 정의합니다.
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class MessageTypeEnum(str, Enum):
    """메시지 유형 열거형"""
    TEXT = "text"
    BUTTON = "button"
    MEDICATION = "medication"
    MOOD = "mood"


class RoleEnum(str, Enum):
    """발화 주체 열거형"""
    USER = "user"
    BOT = "bot"


class ChatRequest(BaseModel):
    """채팅 요청 스키마"""
    user_id: str = Field(..., description="사용자 ID (UUID)")
    message: str = Field(..., min_length=1, max_length=2000, description="사용자 메시지")
    session_id: Optional[str] = Field(None, description="세션 ID")
    message_type: MessageTypeEnum = Field(MessageTypeEnum.TEXT, description="메시지 유형")
    context: Optional[Dict[str, Any]] = Field(None, description="추가 컨텍스트")
    
    @validator('message')
    def validate_message(cls, v):
        if not v.strip():
            raise ValueError('메시지는 필수입니다')
        return v.strip()


class ChatResponse(BaseModel):
    """채팅 응답 스키마"""
    session_id: str = Field(..., description="세션 ID")
    response: str = Field(..., description="봇 응답")
    emotion: Optional[str] = Field(None, description="감지된 감정")
    emotion_score: Optional[float] = Field(None, ge=-1.0, le=1.0, description="감정 점수")
    created_at: datetime = Field(..., description="응답 생성 시간")
    
    # RAG 관련 정보
    context_used: List[str] = Field(default_factory=list, description="사용된 컨텍스트")
    similar_conversations: List[Dict[str, Any]] = Field(default_factory=list, description="유사 대화")
    
    # 추천 액션
    suggested_actions: List[str] = Field(default_factory=list, description="추천 액션")
    
    # 메타데이터
    response_time_ms: Optional[int] = Field(None, description="응답 시간(밀리초)")
    model_used: Optional[str] = Field(None, description="사용된 모델")


class ChatLogSchema(BaseModel):
    """채팅 로그 스키마"""
    id: Optional[int] = None
    user_id: str = Field(..., description="사용자 ID (UUID)")
    role: RoleEnum = Field(..., description="발화 주체")
    message: str = Field(..., description="메시지 내용")
    emotion: Optional[str] = Field(None, description="감정")
    emotion_score: Optional[float] = Field(None, ge=-1.0, le=1.0)
    message_type: MessageTypeEnum = Field(MessageTypeEnum.TEXT)
    session_id: Optional[str] = Field(None)
    qdrant_vector_id: Optional[str] = Field(None, description="벡터 ID")
    created_at: datetime = Field(..., description="생성 시간")
    
    class Config:
        from_attributes = True


class ChatLogCreate(BaseModel):
    """채팅 로그 생성 스키마"""
    user_id: str = Field(..., description="사용자 ID (UUID)")
    role: RoleEnum
    message: str = Field(..., min_length=1, max_length=2000)
    emotion: Optional[str] = Field(None, max_length=20)
    emotion_score: Optional[float] = Field(None, ge=-1.0, le=1.0)
    message_type: MessageTypeEnum = Field(MessageTypeEnum.TEXT)
    session_id: Optional[str] = None


class ChatSessionSchema(BaseModel):
    """채팅 세션 스키마"""
    id: Optional[int] = None
    user_id: str = Field(..., description="사용자 ID (UUID)")
    session_id: str = Field(..., description="세션 ID")
    start_time: datetime = Field(..., description="시작 시간")
    end_time: Optional[datetime] = Field(None, description="종료 시간")
    message_count: int = Field(0, ge=0, description="메시지 수")
    avg_emotion_score: Optional[float] = Field(None, description="평균 감정 점수")
    session_summary: Optional[str] = Field(None, description="세션 요약")
    
    class Config:
        from_attributes = True


class ChatSessionCreate(BaseModel):
    """채팅 세션 생성 스키마"""
    user_id: str = Field(..., description="사용자 ID (UUID)")
    session_id: str = Field(..., min_length=1)


class ChatSessionRequest(BaseModel):
    """채팅 세션 요청 스키마"""
    user_id: str = Field(..., description="사용자 ID (UUID)")
    session_id: Optional[str] = Field(None, description="세션 ID (없으면 새로 생성)")
    action: str = Field("start", description="액션 타입 (start, end, continue)")
    
    @validator('action')
    def validate_action(cls, v):
        if v not in ["start", "end", "continue"]:
            raise ValueError("action은 'start', 'end', 'continue' 중 하나여야 합니다")
        return v


class ChatSessionResponse(BaseModel):
    """채팅 세션 응답 스키마"""
    session_id: str = Field(..., description="세션 ID")
    user_id: str = Field(..., description="사용자 ID (UUID)")
    status: str = Field(..., description="세션 상태")
    message: str = Field(..., description="응답 메시지")
    created_at: datetime = Field(..., description="생성 시간")
    
    class Config:
        from_attributes = True


class ChatVectorPayload(BaseModel):
    """채팅 벡터 페이로드 스키마"""
    user_id: str = Field(..., description="사용자 ID (UUID)")
    session_id: str = Field(..., description="세션 ID")
    message: str = Field(..., description="메시지 내용")
    role: str = Field(..., description="역할 (user/assistant)")
    timestamp: datetime = Field(..., description="타임스탬프")
    emotion: Optional[str] = Field(None, description="감정")
    
    class Config:
        from_attributes = True


class ChatHistoryRequest(BaseModel):
    """채팅 히스토리 요청 스키마"""
    user_id: str = Field(..., description="사용자 ID (UUID)")
    session_id: Optional[str] = Field(None, description="특정 세션만 조회")
    days: int = Field(7, ge=1, le=365, description="조회 기간(일)")
    limit: int = Field(50, ge=1, le=500, description="최대 결과 수")
    offset: int = Field(0, ge=0, description="시작 위치")
    include_bot_messages: bool = Field(True, description="봇 메시지 포함 여부")


class ChatHistoryResponse(BaseModel):
    """채팅 히스토리 응답 스키마"""
    messages: List[ChatLogSchema] = Field(..., description="메시지 목록")
    total_count: int = Field(..., description="전체 메시지 수")
    session_count: int = Field(..., description="세션 수")
    date_range: Dict[str, datetime] = Field(..., description="조회 기간")
    has_more: bool = Field(..., description="더 많은 결과 존재 여부")


class ChatAnalytics(BaseModel):
    """채팅 분석 스키마"""
    user_id: str = Field(..., description="사용자 ID (UUID)")
    period_start: datetime
    period_end: datetime
    
    # 메시지 통계
    total_messages: int = Field(..., description="총 메시지 수")
    user_messages: int = Field(..., description="사용자 메시지 수")
    bot_messages: int = Field(..., description="봇 메시지 수")
    
    # 세션 통계
    total_sessions: int = Field(..., description="총 세션 수")
    avg_session_duration: Optional[float] = Field(None, description="평균 세션 시간(분)")
    avg_messages_per_session: Optional[float] = Field(None, description="세션당 평균 메시지 수")
    
    # 감정 통계
    emotion_distribution: Dict[str, int] = Field(default_factory=dict, description="감정 분포")
    avg_emotion_score: Optional[float] = Field(None, description="평균 감정 점수")
    
    # 활동 패턴
    hourly_activity: Dict[str, int] = Field(default_factory=dict, description="시간대별 활동")
    daily_activity: Dict[str, int] = Field(default_factory=dict, description="일별 활동")
    
    # 주요 키워드
    top_keywords: List[str] = Field(default_factory=list, description="주요 키워드")


class ChatContextSearch(BaseModel):
    """채팅 컨텍스트 검색 스키마"""
    user_id: str = Field(..., description="사용자 ID (UUID)")
    query: str = Field(..., min_length=1, description="검색 쿼리")
    limit: int = Field(5, ge=1, le=20, description="결과 수")
    similarity_threshold: float = Field(0.7, ge=0.0, le=1.0, description="유사도 임계값")
    filters: Optional[Dict[str, Any]] = Field(None, description="추가 필터")


class ChatContextResult(BaseModel):
    """채팅 컨텍스트 검색 결과 스키마"""
    vector_id: str = Field(..., description="벡터 ID")
    message: str = Field(..., description="메시지 내용")
    role: RoleEnum = Field(..., description="발화 주체")
    similarity_score: float = Field(..., description="유사도 점수")
    timestamp: datetime = Field(..., description="메시지 시간")
    emotion: Optional[str] = Field(None, description="감정")
    session_id: Optional[str] = Field(None, description="세션 ID")


class ChatContextResponse(BaseModel):
    """채팅 컨텍스트 응답 스키마"""
    results: List[ChatContextResult] = Field(..., description="검색 결과")
    total_found: int = Field(..., description="총 발견 수")
    search_time_ms: int = Field(..., description="검색 시간(밀리초)")


class ChatPromptContext(BaseModel):
    """GPT 프롬프트 컨텍스트 스키마"""
    user_info: Dict[str, Any] = Field(..., description="사용자 정보")
    conversation_history: List[ChatLogSchema] = Field(default_factory=list, description="대화 기록")
    similar_conversations: List[ChatContextResult] = Field(default_factory=list, description="유사 대화")
    user_interests: List[str] = Field(default_factory=list, description="사용자 관심사")
    recent_emotions: List[str] = Field(default_factory=list, description="최근 감정")
    current_time: datetime = Field(..., description="현재 시간")
    system_instructions: str = Field(..., description="시스템 지시사항")


class ChatGenerationRequest(BaseModel):
    """채팅 생성 요청 스키마"""
    user_message: str = Field(..., description="사용자 메시지")
    context: ChatPromptContext = Field(..., description="컨텍스트")
    model: str = Field("gpt-3.5-turbo", description="사용할 모델")
    max_tokens: int = Field(1000, ge=1, le=4000, description="최대 토큰 수")
    temperature: float = Field(0.7, ge=0.0, le=2.0, description="창의성 정도")


class ChatBatchRequest(BaseModel):
    """채팅 일괄 처리 요청 스키마"""
    user_id: str = Field(..., description="사용자 ID (UUID)")
    messages: List[str] = Field(..., min_items=1, max_items=10, description="메시지 목록")
    session_id: Optional[str] = None


class ChatBatchResponse(BaseModel):
    """채팅 일괄 처리 응답 스키마"""
    session_id: str
    responses: List[ChatResponse] = Field(..., description="응답 목록")
    total_processed: int = Field(..., description="처리된 메시지 수")
    processing_time_ms: int = Field(..., description="총 처리 시간")


class ChatExportRequest(BaseModel):
    """채팅 내보내기 요청 스키마"""
    user_id: str = Field(..., description="사용자 ID (UUID)")
    start_date: Optional[datetime] = Field(None, description="시작 날짜")
    end_date: Optional[datetime] = Field(None, description="종료 날짜")
    format: str = Field("json", pattern="^(json|csv|txt)$", description="내보내기 형식")
    include_emotions: bool = Field(True, description="감정 정보 포함")
    include_metadata: bool = Field(False, description="메타데이터 포함")


class ChatImportRequest(BaseModel):
    """채팅 가져오기 요청 스키마"""
    user_id: str = Field(..., description="사용자 ID (UUID)")
    messages: List[ChatLogCreate] = Field(..., min_items=1, description="가져올 메시지")
    overwrite_existing: bool = Field(False, description="기존 데이터 덮어쓰기")


class ChatStats(BaseModel):
    """채팅 통계 스키마"""
    total_users: int = Field(..., description="총 사용자 수")
    total_messages: int = Field(..., description="총 메시지 수")
    total_sessions: int = Field(..., description="총 세션 수")
    active_users_today: int = Field(..., description="오늘 활성 사용자 수")
    avg_messages_per_user: float = Field(..., description="사용자당 평균 메시지 수")
    most_active_hour: int = Field(..., description="가장 활발한 시간대")
    top_emotions: List[str] = Field(default_factory=list, description="주요 감정")


# 에러 응답 스키마
class ChatError(BaseModel):
    """채팅 에러 스키마"""
    error_code: str = Field(..., description="에러 코드")
    error_message: str = Field(..., description="에러 메시지")
    details: Optional[Dict[str, Any]] = Field(None, description="에러 상세 정보")
    timestamp: datetime = Field(default_factory=datetime.now, description="에러 발생 시간") 