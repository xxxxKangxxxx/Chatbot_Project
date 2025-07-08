"""
Pydantic 스키마 모듈
=====================================================

모든 스키마를 중앙에서 관리합니다.
"""

# 사용자 관련 스키마
from .user import (
    GenderEnum,
    UserBase,
    UserCreate,
    UserUpdate,
    UserResponse,
    UserSummary,
    UserStats,
    UserPreferences,
    UserActivityLog,
    UserLogin,
    UserSearchRequest,
    UserSearchResponse,
    UserProfileUpdate,
    UserDashboard,
    UserMessage,
    UserBulkCreate,
    UserBulkResponse,
)

# 채팅 관련 스키마
from .chat import (
    MessageTypeEnum,
    RoleEnum,
    ChatRequest,
    ChatResponse,
    ChatLogSchema,
    ChatLogCreate,
    ChatSessionSchema,
    ChatSessionCreate,
    ChatHistoryRequest,
    ChatHistoryResponse,
    ChatAnalytics,
    ChatContextSearch,
    ChatContextResult,
    ChatContextResponse,
    ChatPromptContext,
    ChatGenerationRequest,
    ChatBatchRequest,
    ChatBatchResponse,
    ChatExportRequest,
    ChatImportRequest,
    ChatStats,
    ChatError,
)

# 감정 관련 스키마
from .emotion import (
    EmotionTypeEnum,
    DetectionMethodEnum,
    EmotionIntensityEnum,
    EmotionEntry,
    EmotionResponse,
    EmotionCreate,
    EmotionUpdate,
    EmotionSummaryResponse,
    EmotionSummaryCreate,
    EmotionAnalysisRequest,
    EmotionAnalysisResponse,
    EmotionHistoryRequest,
    EmotionHistoryResponse,
    EmotionTrendAnalysis,
    EmotionCorrelation,
    EmotionAlert,
    EmotionGoal,
    EmotionInsight,
    EmotionExportRequest,
    EmotionBatchAnalysis,
    EmotionBatchAnalysisResponse,
    EmotionCalendar,
    EmotionMessage,
)

# 일정 관리 관련 스키마
from .schedule import (
    ScheduleType,
    ScheduleStatus,
    RecurrenceType,
    Priority,
    LogStatus,
    ScheduleBase,
    ScheduleCreate,
    ScheduleUpdate,
    ScheduleResponse,
    ScheduleLogBase,
    ScheduleLogCreate,
    ScheduleLogUpdate,
    ScheduleLogResponse,
    ReminderResponse,
    ScheduleStatsResponse,
    ComplianceResponse,
    CalendarDayResponse,
    CalendarWeekResponse,
    CalendarMonthResponse,
    ScheduleSearchRequest,
    ScheduleListResponse,
    ScheduleBatchRequest,
    ScheduleBatchResponse,
    ScheduleTemplateCreate,
    ScheduleTemplateResponse,
    ScheduleInsightResponse,
)

# 관심사 관련 스키마
from .interest import (
    InterestCategoryEnum,
    TrendTypeEnum,
    InterestKeyword,
    InterestCreate,
    InterestResponse,
    InterestUpdate,
    InterestTrendResponse,
    InterestTrendCreate,
    InterestAnalysis,
    InterestRecommendation,
    InterestCorrelation,
    InterestProfile,
    InterestSearch,
    InterestSearchResponse,
    InterestKeywordSuggestion,
    InterestKeywordSuggestionResponse,
    InterestBatchUpdate,
    InterestBatchUpdateResponse,
    InterestExportRequest,
    InterestImportRequest,
    InterestCalendar,
    InterestInsight,
    InterestStats,
    InterestMessage,
)

# 공통 응답 스키마
from pydantic import BaseModel, Field
from typing import Optional, Any, List
from datetime import datetime


class BaseResponse(BaseModel):
    """기본 응답 스키마"""
    success: bool = Field(True, description="성공 여부")
    message: str = Field("", description="응답 메시지")
    data: Optional[Any] = Field(None, description="응답 데이터")
    timestamp: datetime = Field(default_factory=datetime.now, description="응답 시간")


class ErrorResponse(BaseModel):
    """에러 응답 스키마"""
    success: bool = Field(False, description="성공 여부")
    error_code: str = Field(..., description="에러 코드")
    error_message: str = Field(..., description="에러 메시지")
    details: Optional[dict] = Field(None, description="에러 상세 정보")
    timestamp: datetime = Field(default_factory=datetime.now, description="에러 발생 시간")


class PaginatedResponse(BaseModel):
    """페이지네이션 응답 스키마"""
    items: List[Any] = Field(..., description="아이템 목록")
    total_count: int = Field(..., description="전체 아이템 수")
    page: int = Field(..., description="현재 페이지")
    page_size: int = Field(..., description="페이지 크기")
    total_pages: int = Field(..., description="전체 페이지 수")
    has_next: bool = Field(..., description="다음 페이지 존재 여부")
    has_previous: bool = Field(..., description="이전 페이지 존재 여부")


class HealthCheckResponse(BaseModel):
    """헬스 체크 응답 스키마"""
    status: str = Field("healthy", description="서비스 상태")
    version: str = Field("1.0.0", description="API 버전")
    timestamp: datetime = Field(default_factory=datetime.now, description="체크 시간")
    database_status: str = Field("connected", description="데이터베이스 상태")
    qdrant_status: str = Field("connected", description="Qdrant 상태")
    openai_status: str = Field("connected", description="OpenAI 상태")


class BulkOperationResponse(BaseModel):
    """일괄 작업 응답 스키마"""
    total_items: int = Field(..., description="총 아이템 수")
    successful_items: int = Field(..., description="성공한 아이템 수")
    failed_items: int = Field(..., description="실패한 아이템 수")
    errors: List[str] = Field(default_factory=list, description="에러 목록")
    warnings: List[str] = Field(default_factory=list, description="경고 목록")
    processing_time_ms: int = Field(..., description="처리 시간(밀리초)")


class ValidationError(BaseModel):
    """유효성 검증 에러 스키마"""
    field: str = Field(..., description="필드명")
    message: str = Field(..., description="에러 메시지")
    invalid_value: Optional[Any] = Field(None, description="잘못된 값")


class ValidationErrorResponse(BaseModel):
    """유효성 검증 에러 응답 스키마"""
    success: bool = Field(False, description="성공 여부")
    error_code: str = Field("VALIDATION_ERROR", description="에러 코드")
    error_message: str = Field("입력 데이터가 유효하지 않습니다", description="에러 메시지")
    validation_errors: List[ValidationError] = Field(..., description="유효성 검증 에러 목록")
    timestamp: datetime = Field(default_factory=datetime.now, description="에러 발생 시간")


__all__ = [
    # 기본 열거형
    "GenderEnum",
    "MessageTypeEnum",
    "RoleEnum",
    "EmotionTypeEnum",
    "DetectionMethodEnum",
    "EmotionIntensityEnum",
    "MedicationTypeEnum",
    "FrequencyEnum",
    "ReminderTypeEnum",
    "ComplianceStatusEnum",
    "InterestCategoryEnum",
    "TrendTypeEnum",
    
    # 사용자 스키마
    "UserBase",
    "UserCreate",
    "UserUpdate",
    "UserResponse",
    "UserSummary",
    "UserStats",
    "UserPreferences",
    "UserActivityLog",
    "UserLogin",
    "UserSearchRequest",
    "UserSearchResponse",
    "UserProfileUpdate",
    "UserDashboard",
    "UserMessage",
    "UserBulkCreate",
    "UserBulkResponse",
    
    # 채팅 스키마
    "ChatRequest",
    "ChatResponse",
    "ChatLogSchema",
    "ChatLogCreate",
    "ChatSessionSchema",
    "ChatSessionCreate",
    "ChatHistoryRequest",
    "ChatHistoryResponse",
    "ChatAnalytics",
    "ChatContextSearch",
    "ChatContextResult",
    "ChatContextResponse",
    "ChatPromptContext",
    "ChatGenerationRequest",
    "ChatBatchRequest",
    "ChatBatchResponse",
    "ChatExportRequest",
    "ChatImportRequest",
    "ChatStats",
    "ChatError",
    
    # 감정 스키마
    "EmotionEntry",
    "EmotionResponse",
    "EmotionCreate",
    "EmotionUpdate",
    "EmotionSummaryResponse",
    "EmotionSummaryCreate",
    "EmotionAnalysisRequest",
    "EmotionAnalysisResponse",
    "EmotionHistoryRequest",
    "EmotionHistoryResponse",
    "EmotionTrendAnalysis",
    "EmotionCorrelation",
    "EmotionAlert",
    "EmotionGoal",
    "EmotionInsight",
    "EmotionExportRequest",
    "EmotionBatchAnalysis",
    "EmotionBatchAnalysisResponse",
    "EmotionCalendar",
    "EmotionMessage",
    
    # 약물 스키마
    "MedicationScheduleCreate",
    "MedicationScheduleResponse",
    "MedicationScheduleUpdate",
    "MedicationCheck",
    "MedicationHistoryResponse",
    "MedicationReminderCreate",
    "MedicationReminderResponse",
    "MedicationComplianceReport",
    "MedicationInteractionCheck",
    "MedicationInteractionResponse",
    "MedicationInventory",
    "MedicationAlert",
    "MedicationProfile",
    "MedicationCalendar",
    "MedicationExportRequest",
    "MedicationImportRequest",
    "MedicationSearch",
    "MedicationSearchResult",
    "MedicationBatchUpdate",
    "MedicationStats",
    "MedicationMessage",
    
    # 관심사 스키마
    "InterestKeyword",
    "InterestCreate",
    "InterestResponse",
    "InterestUpdate",
    "InterestTrendResponse",
    "InterestTrendCreate",
    "InterestAnalysis",
    "InterestRecommendation",
    "InterestCorrelation",
    "InterestProfile",
    "InterestSearch",
    "InterestSearchResponse",
    "InterestKeywordSuggestion",
    "InterestKeywordSuggestionResponse",
    "InterestBatchUpdate",
    "InterestBatchUpdateResponse",
    "InterestExportRequest",
    "InterestImportRequest",
    "InterestCalendar",
    "InterestInsight",
    "InterestStats",
    "InterestMessage",
    
    # 공통 응답 스키마
    "BaseResponse",
    "ErrorResponse",
    "PaginatedResponse",
    "HealthCheckResponse",
    "BulkOperationResponse",
    "ValidationError",
    "ValidationErrorResponse",
] 