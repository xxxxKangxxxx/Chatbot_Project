"""
감정 관련 Pydantic 스키마
=====================================================

감정 분석, 기록, 요약 모델을 정의합니다.
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class EmotionTypeEnum(str, Enum):
    """감정 유형 열거형"""
    HAPPY = "happy"
    SAD = "sad"
    ANGRY = "angry"
    ANXIOUS = "anxious"
    EXCITED = "excited"
    CALM = "calm"
    LONELY = "lonely"
    GRATEFUL = "grateful"
    WORRIED = "worried"
    CONTENT = "content"
    FRUSTRATED = "frustrated"
    HOPEFUL = "hopeful"


class DetectionMethodEnum(str, Enum):
    """감정 감지 방법 열거형"""
    GPT_ANALYSIS = "gpt_analysis"
    KEYWORD_MATCHING = "keyword_matching"
    USER_INPUT = "user_input"
    SENTIMENT_MODEL = "sentiment_model"


class EmotionIntensityEnum(str, Enum):
    """감정 강도 열거형"""
    VERY_LOW = "very_low"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


class EmotionEntry(BaseModel):
    """감정 기록 스키마"""
    user_id: int = Field(..., gt=0, description="사용자 ID")
    emotion_type: EmotionTypeEnum = Field(..., description="감정 유형")
    intensity: EmotionIntensityEnum = Field(..., description="감정 강도")
    score: float = Field(..., ge=-1.0, le=1.0, description="감정 점수")
    detection_method: DetectionMethodEnum = Field(..., description="감지 방법")
    context: Optional[str] = Field(None, max_length=1000, description="감정 발생 맥락")
    triggers: List[str] = Field(default_factory=list, description="감정 유발 요인")
    notes: Optional[str] = Field(None, max_length=500, description="추가 메모")
    
    @validator('score')
    def validate_score_range(cls, v):
        if not -1.0 <= v <= 1.0:
            raise ValueError('감정 점수는 -1.0에서 1.0 사이여야 합니다')
        return v


class EmotionResponse(BaseModel):
    """감정 응답 스키마"""
    id: int
    user_id: int
    emotion_type: EmotionTypeEnum
    intensity: EmotionIntensityEnum
    score: float
    detection_method: DetectionMethodEnum
    context: Optional[str]
    triggers: List[str]
    notes: Optional[str]
    color_code: str = Field(..., description="감정 색상 코드")
    emoji: str = Field(..., description="감정 이모지")
    created_at: datetime
    
    class Config:
        from_attributes = True


class EmotionCreate(BaseModel):
    """감정 생성 스키마"""
    user_id: int = Field(..., gt=0)
    emotion_type: EmotionTypeEnum
    intensity: EmotionIntensityEnum = Field(EmotionIntensityEnum.MEDIUM)
    score: float = Field(..., ge=-1.0, le=1.0)
    detection_method: DetectionMethodEnum = Field(DetectionMethodEnum.GPT_ANALYSIS)
    context: Optional[str] = Field(None, max_length=1000)
    triggers: List[str] = Field(default_factory=list)
    notes: Optional[str] = Field(None, max_length=500)


class EmotionUpdate(BaseModel):
    """감정 업데이트 스키마"""
    emotion_type: Optional[EmotionTypeEnum] = None
    intensity: Optional[EmotionIntensityEnum] = None
    score: Optional[float] = Field(None, ge=-1.0, le=1.0)
    context: Optional[str] = Field(None, max_length=1000)
    triggers: Optional[List[str]] = None
    notes: Optional[str] = Field(None, max_length=500)


class EmotionSummaryResponse(BaseModel):
    """감정 요약 응답 스키마"""
    id: int
    user_id: int
    date: datetime = Field(..., description="요약 날짜")
    dominant_emotion: EmotionTypeEnum = Field(..., description="주요 감정")
    avg_score: float = Field(..., description="평균 감정 점수")
    emotion_count: int = Field(..., description="감정 기록 수")
    emotion_distribution: Dict[str, int] = Field(..., description="감정 분포")
    mood_trend: str = Field(..., description="기분 변화 추세")
    summary_text: Optional[str] = Field(None, description="요약 텍스트")
    
    class Config:
        from_attributes = True


class EmotionSummaryCreate(BaseModel):
    """감정 요약 생성 스키마"""
    user_id: int = Field(..., gt=0)
    date: datetime
    dominant_emotion: EmotionTypeEnum
    avg_score: float = Field(..., ge=-1.0, le=1.0)
    emotion_count: int = Field(..., ge=0)
    emotion_distribution: Dict[str, int] = Field(default_factory=dict)
    mood_trend: str = Field(..., max_length=50)
    summary_text: Optional[str] = Field(None, max_length=1000)


class EmotionAnalysisRequest(BaseModel):
    """감정 분석 요청 스키마"""
    user_id: int = Field(..., gt=0)
    text: str = Field(..., min_length=1, max_length=2000, description="분석할 텍스트")
    context: Optional[str] = Field(None, description="추가 컨텍스트")
    method: DetectionMethodEnum = Field(DetectionMethodEnum.GPT_ANALYSIS)
    
    @validator('text')
    def validate_text(cls, v):
        if not v.strip():
            raise ValueError('분석할 텍스트는 필수입니다')
        return v.strip()


class EmotionAnalysisResponse(BaseModel):
    """감정 분석 응답 스키마"""
    emotion_type: EmotionTypeEnum = Field(..., description="감지된 감정")
    intensity: EmotionIntensityEnum = Field(..., description="감정 강도")
    score: float = Field(..., description="감정 점수")
    confidence: float = Field(..., ge=0.0, le=1.0, description="신뢰도")
    keywords: List[str] = Field(default_factory=list, description="감정 키워드")
    explanation: str = Field(..., description="분석 설명")
    suggestions: List[str] = Field(default_factory=list, description="대응 제안")
    processing_time_ms: int = Field(..., description="처리 시간")


class EmotionAnalysisResult(BaseModel):
    """감정 분석 결과 스키마 (서비스 레이어용)"""
    primary_emotion: EmotionTypeEnum = Field(..., description="주요 감정")
    intensity: float = Field(..., ge=0.0, le=1.0, description="감정 강도")
    confidence: float = Field(..., ge=0.0, le=1.0, description="신뢰도")
    detected_keywords: List[str] = Field(default_factory=list, description="감지된 키워드")
    analysis_method: str = Field("ai_analysis", description="분석 방법")
    timestamp: datetime = Field(default_factory=datetime.now, description="분석 시간")
    
    class Config:
        from_attributes = True


class EmotionHistoryRequest(BaseModel):
    """감정 히스토리 요청 스키마"""
    user_id: int = Field(..., gt=0)
    start_date: Optional[datetime] = Field(None, description="시작 날짜")
    end_date: Optional[datetime] = Field(None, description="종료 날짜")
    emotion_types: Optional[List[EmotionTypeEnum]] = Field(None, description="필터할 감정 유형")
    intensity_min: Optional[EmotionIntensityEnum] = Field(None, description="최소 강도")
    limit: int = Field(50, ge=1, le=500, description="최대 결과 수")
    offset: int = Field(0, ge=0, description="시작 위치")
    include_summaries: bool = Field(True, description="요약 포함 여부")


class EmotionHistoryResponse(BaseModel):
    """감정 히스토리 응답 스키마"""
    emotions: List[EmotionResponse] = Field(..., description="감정 기록")
    summaries: List[EmotionSummaryResponse] = Field(default_factory=list, description="감정 요약")
    total_count: int = Field(..., description="전체 기록 수")
    date_range: Dict[str, datetime] = Field(..., description="조회 기간")
    statistics: Dict[str, Any] = Field(..., description="통계 정보")
    has_more: bool = Field(..., description="더 많은 결과 존재 여부")


class EmotionTrendAnalysis(BaseModel):
    """감정 트렌드 분석 스키마"""
    user_id: int
    period_start: datetime
    period_end: datetime
    
    # 전체 통계
    total_entries: int = Field(..., description="총 감정 기록 수")
    avg_score: float = Field(..., description="평균 감정 점수")
    score_trend: str = Field(..., description="점수 변화 추세")
    
    # 감정 분포
    emotion_distribution: Dict[str, int] = Field(..., description="감정 분포")
    intensity_distribution: Dict[str, int] = Field(..., description="강도 분포")
    
    # 시간대별 분석
    hourly_patterns: Dict[str, float] = Field(default_factory=dict, description="시간대별 패턴")
    daily_patterns: Dict[str, float] = Field(default_factory=dict, description="일별 패턴")
    weekly_patterns: Dict[str, float] = Field(default_factory=dict, description="주별 패턴")
    
    # 주요 트리거
    top_triggers: List[str] = Field(default_factory=list, description="주요 트리거")
    trigger_frequency: Dict[str, int] = Field(default_factory=dict, description="트리거 빈도")
    
    # 개선 제안
    recommendations: List[str] = Field(default_factory=list, description="개선 제안")
    risk_factors: List[str] = Field(default_factory=list, description="위험 요소")


class EmotionCorrelation(BaseModel):
    """감정 상관관계 분석 스키마"""
    user_id: int
    emotion_pairs: List[Dict[str, Any]] = Field(..., description="감정 쌍별 상관관계")
    time_correlations: Dict[str, float] = Field(..., description="시간대별 상관관계")
    trigger_correlations: Dict[str, float] = Field(..., description="트리거별 상관관계")
    strongest_correlations: List[str] = Field(..., description="가장 강한 상관관계")
    insights: List[str] = Field(default_factory=list, description="인사이트")


class EmotionAlert(BaseModel):
    """감정 알림 스키마"""
    user_id: int
    alert_type: str = Field(..., description="알림 유형")
    emotion_type: EmotionTypeEnum = Field(..., description="관련 감정")
    severity: str = Field(..., description="심각도")
    message: str = Field(..., description="알림 메시지")
    recommendations: List[str] = Field(default_factory=list, description="권장사항")
    created_at: datetime = Field(default_factory=datetime.now)
    is_acknowledged: bool = Field(False, description="확인 여부")


class EmotionGoal(BaseModel):
    """감정 목표 스키마"""
    user_id: int
    goal_type: str = Field(..., description="목표 유형")
    target_emotion: EmotionTypeEnum = Field(..., description="목표 감정")
    target_score: float = Field(..., ge=-1.0, le=1.0, description="목표 점수")
    target_frequency: int = Field(..., ge=0, description="목표 빈도")
    deadline: Optional[datetime] = Field(None, description="목표 달성 기한")
    progress: float = Field(0.0, ge=0.0, le=1.0, description="진행률")
    is_active: bool = Field(True, description="활성 여부")
    created_at: datetime = Field(default_factory=datetime.now)


class EmotionInsight(BaseModel):
    """감정 인사이트 스키마"""
    user_id: int
    insight_type: str = Field(..., description="인사이트 유형")
    title: str = Field(..., description="인사이트 제목")
    description: str = Field(..., description="인사이트 설명")
    data_points: List[Dict[str, Any]] = Field(..., description="데이터 포인트")
    actionable_items: List[str] = Field(default_factory=list, description="실행 가능한 항목")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="신뢰도")
    created_at: datetime = Field(default_factory=datetime.now)


class EmotionExportRequest(BaseModel):
    """감정 데이터 내보내기 요청 스키마"""
    user_id: int = Field(..., gt=0)
    start_date: Optional[datetime] = Field(None)
    end_date: Optional[datetime] = Field(None)
    format: str = Field("json", pattern="^(json|csv|xlsx)$", description="내보내기 형식")
    include_summaries: bool = Field(True, description="요약 포함 여부")
    include_analysis: bool = Field(False, description="분석 포함 여부")
    anonymize: bool = Field(False, description="익명화 여부")


class EmotionBatchAnalysis(BaseModel):
    """감정 일괄 분석 스키마"""
    user_id: int = Field(..., gt=0)
    texts: List[str] = Field(..., min_items=1, max_items=50, description="분석할 텍스트 목록")
    context: Optional[str] = Field(None, description="공통 컨텍스트")
    method: DetectionMethodEnum = Field(DetectionMethodEnum.GPT_ANALYSIS)


class EmotionBatchAnalysisResponse(BaseModel):
    """감정 일괄 분석 응답 스키마"""
    results: List[EmotionAnalysisResponse] = Field(..., description="분석 결과")
    summary: Dict[str, Any] = Field(..., description="전체 요약")
    processing_time_ms: int = Field(..., description="총 처리 시간")
    success_count: int = Field(..., description="성공 건수")
    error_count: int = Field(..., description="오류 건수")


class EmotionCalendar(BaseModel):
    """감정 캘린더 스키마"""
    user_id: int
    year: int = Field(..., ge=2020, le=2030)
    month: int = Field(..., ge=1, le=12)
    daily_emotions: Dict[str, Dict[str, Any]] = Field(..., description="일별 감정 데이터")
    monthly_summary: Dict[str, Any] = Field(..., description="월별 요약")
    mood_calendar: List[List[str]] = Field(..., description="기분 캘린더 그리드")


# 응답 메시지 스키마
class EmotionMessage(BaseModel):
    """감정 관련 메시지 스키마"""
    message: str
    success: bool = True
    data: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.now)


class EmotionStatsResponse(BaseModel):
    """감정 통계 응답 스키마"""
    user_id: str
    stats_period: Dict[str, datetime] = Field(..., description="통계 기간")
    total_emotions: int = Field(..., description="총 감정 기록 수")
    emotion_distribution: Dict[str, int] = Field(..., description="감정별 분포")
    avg_intensity: float = Field(..., description="평균 감정 강도")
    dominant_emotion: str = Field(..., description="주요 감정")
    emotion_frequency: Dict[str, float] = Field(..., description="감정 빈도")
    mood_stability: float = Field(..., description="기분 안정성 지수")
    positive_ratio: float = Field(..., description="긍정 감정 비율")
    emotional_range: float = Field(..., description="감정 범위")
    
    class Config:
        from_attributes = True


class EmotionPatternResponse(BaseModel):
    """감정 패턴 응답 스키마"""
    user_id: str
    analysis_period: Dict[str, datetime] = Field(..., description="분석 기간")
    daily_patterns: Dict[str, Any] = Field(..., description="일일 패턴")
    weekly_patterns: Dict[str, Any] = Field(..., description="주간 패턴")
    emotional_triggers: List[str] = Field(default_factory=list, description="감정 트리거")
    pattern_insights: List[str] = Field(default_factory=list, description="패턴 인사이트")
    cyclical_patterns: Dict[str, Any] = Field(default_factory=dict, description="주기적 패턴")
    anomalies: List[Dict[str, Any]] = Field(default_factory=list, description="이상 패턴")
    recommendations: List[str] = Field(default_factory=list, description="개선 권장사항")
    
    class Config:
        from_attributes = True 