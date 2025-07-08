"""
관심사 관련 Pydantic 스키마
=====================================================

사용자 관심사, 키워드, 트렌드 모델을 정의합니다.
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class InterestCategoryEnum(str, Enum):
    """관심사 카테고리 열거형"""
    HEALTH = "health"
    FOOD = "food"
    HOBBY = "hobby"
    FAMILY = "family"
    TRAVEL = "travel"
    ENTERTAINMENT = "entertainment"
    TECHNOLOGY = "technology"
    SPORTS = "sports"
    CULTURE = "culture"
    EDUCATION = "education"
    FINANCE = "finance"
    SOCIAL = "social"
    NATURE = "nature"
    RELIGION = "religion"
    POLITICS = "politics"
    OTHER = "other"


class TrendTypeEnum(str, Enum):
    """트렌드 유형 열거형"""
    RISING = "rising"
    STABLE = "stable"
    DECLINING = "declining"
    SEASONAL = "seasonal"
    EMERGING = "emerging"


class InterestKeyword(BaseModel):
    """관심사 키워드 스키마"""
    keyword: str = Field(..., min_length=1, max_length=50, description="키워드")
    category: InterestCategoryEnum = Field(..., description="카테고리")
    weight: float = Field(1.0, ge=0.0, le=10.0, description="가중치")
    
    @validator('keyword')
    def validate_keyword(cls, v):
        if not v.strip():
            raise ValueError('키워드는 필수입니다')
        return v.strip().lower()


class InterestCreate(BaseModel):
    """관심사 생성 스키마"""
    user_id: str = Field(..., description="사용자 ID")
    keyword: str = Field(..., min_length=1, max_length=50, description="관심사 키워드")
    category: InterestCategoryEnum = Field(..., description="카테고리")
    weight: float = Field(1.0, ge=0.0, le=10.0, description="가중치")
    
    @validator('keyword')
    def validate_keyword(cls, v):
        if not v.strip():
            raise ValueError('키워드는 필수입니다')
        return v.strip().lower()


class InterestResponse(BaseModel):
    """관심사 응답 스키마"""
    id: str
    user_id: str
    keyword: str
    category: InterestCategoryEnum
    weight: float
    mentioned_count: int
    last_mentioned: Optional[datetime]
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class InterestUpdate(BaseModel):
    """관심사 업데이트 스키마"""
    keyword: Optional[str] = Field(None, min_length=1, max_length=50)
    category: Optional[InterestCategoryEnum] = None
    weight: Optional[float] = Field(None, ge=0.0, le=10.0)
    is_active: Optional[bool] = None
    context: Optional[str] = Field(None, max_length=500)


class InterestTrendResponse(BaseModel):
    """관심사 트렌드 응답 스키마"""
    id: int
    user_id: int
    keyword: str
    category: InterestCategoryEnum
    trend_type: TrendTypeEnum
    score_change: float
    period_start: datetime
    period_end: datetime
    data_points: List[Dict[str, Any]]
    insights: List[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


class InterestTrendCreate(BaseModel):
    """관심사 트렌드 생성 스키마"""
    user_id: int = Field(..., gt=0)
    keyword: str = Field(..., min_length=1, max_length=50)
    category: InterestCategoryEnum
    trend_type: TrendTypeEnum
    score_change: float = Field(..., ge=-10.0, le=10.0)
    period_start: datetime
    period_end: datetime
    data_points: List[Dict[str, Any]] = Field(default_factory=list)
    insights: List[str] = Field(default_factory=list)


class InterestAnalysis(BaseModel):
    """관심사 분석 스키마"""
    user_id: int
    analysis_date: datetime
    
    # 전체 통계
    total_interests: int = Field(..., description="총 관심사 수")
    active_interests: int = Field(..., description="활성 관심사 수")
    avg_weight: float = Field(..., description="평균 가중치")
    
    # 카테고리별 분석
    category_distribution: Dict[str, int] = Field(..., description="카테고리별 분포")
    top_categories: List[str] = Field(..., description="주요 카테고리")
    
    # 트렌드 분석
    rising_interests: List[str] = Field(default_factory=list, description="증가하는 관심사")
    declining_interests: List[str] = Field(default_factory=list, description="감소하는 관심사")
    stable_interests: List[str] = Field(default_factory=list, description="안정적인 관심사")
    
    # 시간대별 패턴
    mention_patterns: Dict[str, Any] = Field(default_factory=dict, description="언급 패턴")
    seasonal_trends: Dict[str, Any] = Field(default_factory=dict, description="계절별 트렌드")
    
    # 추천 및 인사이트
    recommendations: List[str] = Field(default_factory=list, description="추천사항")
    insights: List[str] = Field(default_factory=list, description="인사이트")


class InterestRecommendation(BaseModel):
    """관심사 추천 스키마"""
    user_id: int
    recommended_keywords: List[str] = Field(..., description="추천 키워드")
    recommendation_reasons: Dict[str, str] = Field(..., description="추천 이유")
    confidence_scores: Dict[str, float] = Field(..., description="신뢰도 점수")
    related_interests: Dict[str, List[str]] = Field(..., description="관련 관심사")
    suggested_categories: List[InterestCategoryEnum] = Field(..., description="추천 카테고리")
    
    # 메타데이터
    algorithm_used: str = Field(..., description="사용된 알고리즘")
    generated_at: datetime = Field(default_factory=datetime.now)
    expires_at: Optional[datetime] = Field(None, description="만료 시간")


class InterestCorrelation(BaseModel):
    """관심사 상관관계 스키마"""
    user_id: int
    keyword_pairs: List[Dict[str, Any]] = Field(..., description="키워드 쌍별 상관관계")
    category_correlations: Dict[str, Dict[str, float]] = Field(..., description="카테고리 간 상관관계")
    temporal_correlations: Dict[str, float] = Field(..., description="시간적 상관관계")
    strongest_correlations: List[str] = Field(..., description="가장 강한 상관관계")
    
    # 분석 결과
    correlation_insights: List[str] = Field(default_factory=list, description="상관관계 인사이트")
    suggested_connections: List[str] = Field(default_factory=list, description="제안된 연결")
    analysis_confidence: float = Field(..., ge=0.0, le=1.0, description="분석 신뢰도")


class InterestProfile(BaseModel):
    """사용자 관심사 프로필 스키마"""
    user_id: int
    interests: List[InterestResponse] = Field(..., description="관심사 목록")
    dominant_categories: List[str] = Field(..., description="주요 카테고리")
    interest_diversity_score: float = Field(..., description="관심사 다양성 점수")
    engagement_level: str = Field(..., description="참여 수준")
    
    # 시간대별 활동
    activity_patterns: Dict[str, Any] = Field(default_factory=dict, description="활동 패턴")
    peak_interest_times: List[str] = Field(default_factory=list, description="관심사 피크 시간")
    
    # 개인화 정보
    personalization_data: Dict[str, Any] = Field(default_factory=dict, description="개인화 데이터")
    content_preferences: Dict[str, Any] = Field(default_factory=dict, description="콘텐츠 선호도")


class InterestSearch(BaseModel):
    """관심사 검색 스키마"""
    user_id: Optional[int] = Field(None, gt=0)
    query: str = Field(..., min_length=1, description="검색어")
    categories: Optional[List[InterestCategoryEnum]] = Field(None, description="카테고리 필터")
    min_weight: Optional[float] = Field(None, ge=0.0, description="최소 가중치")
    max_weight: Optional[float] = Field(None, le=10.0, description="최대 가중치")
    include_inactive: bool = Field(False, description="비활성 관심사 포함")
    limit: int = Field(20, ge=1, le=100, description="결과 수")
    offset: int = Field(0, ge=0, description="시작 위치")
    
    @validator('max_weight')
    def validate_weight_range(cls, v, values):
        min_weight = values.get('min_weight')
        if min_weight is not None and v is not None and v < min_weight:
            raise ValueError('최대 가중치는 최소 가중치보다 커야 합니다')
        return v


class InterestSearchResponse(BaseModel):
    """관심사 검색 응답 스키마"""
    interests: List[InterestResponse] = Field(..., description="검색 결과")
    total_count: int = Field(..., description="총 결과 수")
    categories_found: List[str] = Field(..., description="발견된 카테고리")
    search_suggestions: List[str] = Field(default_factory=list, description="검색 제안")
    has_more: bool = Field(..., description="더 많은 결과 존재 여부")


class InterestKeywordSuggestion(BaseModel):
    """관심사 키워드 제안 스키마"""
    text: str = Field(..., description="분석할 텍스트")
    user_id: Optional[int] = Field(None, gt=0, description="사용자 ID")
    context: Optional[str] = Field(None, description="컨텍스트")
    extract_new_only: bool = Field(False, description="새로운 키워드만 추출")


class InterestKeywordSuggestionResponse(BaseModel):
    """관심사 키워드 제안 응답 스키마"""
    suggested_keywords: List[InterestKeyword] = Field(..., description="제안된 키워드")
    confidence_scores: Dict[str, float] = Field(..., description="신뢰도 점수")
    extraction_method: str = Field(..., description="추출 방법")
    processing_time_ms: int = Field(..., description="처리 시간")
    
    # 분석 결과
    text_analysis: Dict[str, Any] = Field(default_factory=dict, description="텍스트 분석")
    keyword_density: Dict[str, float] = Field(default_factory=dict, description="키워드 밀도")
    topic_classification: List[str] = Field(default_factory=list, description="주제 분류")


class InterestBatchUpdate(BaseModel):
    """관심사 일괄 업데이트 스키마"""
    user_id: int = Field(..., gt=0)
    updates: List[Dict[str, Any]] = Field(..., min_items=1, description="업데이트 목록")
    merge_duplicates: bool = Field(True, description="중복 항목 병합")
    auto_categorize: bool = Field(True, description="자동 카테고리 분류")


class InterestBatchUpdateResponse(BaseModel):
    """관심사 일괄 업데이트 응답 스키마"""
    updated_count: int = Field(..., description="업데이트된 항목 수")
    created_count: int = Field(..., description="생성된 항목 수")
    merged_count: int = Field(..., description="병합된 항목 수")
    error_count: int = Field(..., description="오류 항목 수")
    
    # 결과 상세
    updated_interests: List[InterestResponse] = Field(..., description="업데이트된 관심사")
    errors: List[str] = Field(default_factory=list, description="오류 목록")
    warnings: List[str] = Field(default_factory=list, description="경고 목록")


class InterestExportRequest(BaseModel):
    """관심사 데이터 내보내기 요청 스키마"""
    user_id: int = Field(..., gt=0)
    categories: Optional[List[InterestCategoryEnum]] = Field(None, description="카테고리 필터")
    include_trends: bool = Field(True, description="트렌드 포함")
    include_correlations: bool = Field(False, description="상관관계 포함")
    format: str = Field("json", pattern="^(json|csv|xlsx)$", description="내보내기 형식")
    date_range: Optional[Dict[str, datetime]] = Field(None, description="날짜 범위")


class InterestImportRequest(BaseModel):
    """관심사 데이터 가져오기 요청 스키마"""
    user_id: int = Field(..., gt=0)
    interests: List[InterestCreate] = Field(..., min_items=1, description="가져올 관심사")
    merge_strategy: str = Field("update", pattern="^(update|replace|skip)$", description="병합 전략")
    auto_weight: bool = Field(True, description="자동 가중치 계산")


class InterestCalendar(BaseModel):
    """관심사 캘린더 스키마"""
    user_id: int
    year: int = Field(..., ge=2020, le=2030)
    month: int = Field(..., ge=1, le=12)
    daily_interests: Dict[str, List[str]] = Field(..., description="일별 관심사")
    interest_heatmap: List[List[int]] = Field(..., description="관심사 히트맵")
    monthly_trends: Dict[str, Any] = Field(..., description="월별 트렌드")
    top_interests_by_day: Dict[str, List[str]] = Field(..., description="일별 주요 관심사")


class InterestInsight(BaseModel):
    """관심사 인사이트 스키마"""
    user_id: int
    insight_type: str = Field(..., description="인사이트 유형")
    title: str = Field(..., description="인사이트 제목")
    description: str = Field(..., description="인사이트 설명")
    related_interests: List[str] = Field(..., description="관련 관심사")
    data_points: List[Dict[str, Any]] = Field(..., description="데이터 포인트")
    actionable_recommendations: List[str] = Field(default_factory=list, description="실행 가능한 추천")
    confidence_level: float = Field(..., ge=0.0, le=1.0, description="신뢰도")
    generated_at: datetime = Field(default_factory=datetime.now)


class InterestStats(BaseModel):
    """관심사 통계 스키마"""
    total_users: int = Field(..., description="총 사용자 수")
    total_interests: int = Field(..., description="총 관심사 수")
    unique_keywords: int = Field(..., description="고유 키워드 수")
    avg_interests_per_user: float = Field(..., description="사용자당 평균 관심사 수")
    
    # 카테고리 통계
    category_distribution: Dict[str, int] = Field(..., description="카테고리별 분포")
    most_popular_categories: List[str] = Field(..., description="가장 인기 있는 카테고리")
    
    # 트렌드 통계
    trending_keywords: List[str] = Field(..., description="트렌딩 키워드")
    seasonal_patterns: Dict[str, Any] = Field(..., description="계절별 패턴")
    
    # 참여도 통계
    engagement_metrics: Dict[str, float] = Field(..., description="참여도 지표")
    user_activity_levels: Dict[str, int] = Field(..., description="사용자 활동 수준")


# 응답 메시지 스키마
class InterestMessage(BaseModel):
    """관심사 관련 메시지 스키마"""
    message: str
    success: bool = True
    data: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.now)


class InterestAnalysisResponse(BaseModel):
    """관심사 분석 응답 스키마"""
    user_id: str
    analysis_period: Dict[str, datetime] = Field(..., description="분석 기간")
    total_interests: int = Field(..., description="총 관심사 수")
    active_interests: int = Field(..., description="활성 관심사 수")
    category_distribution: Dict[str, int] = Field(..., description="카테고리별 분포")
    top_interests: List[str] = Field(..., description="주요 관심사")
    emerging_interests: List[str] = Field(default_factory=list, description="신규 관심사")
    declining_interests: List[str] = Field(default_factory=list, description="감소 관심사")
    insights: List[str] = Field(default_factory=list, description="분석 인사이트")
    recommendations: List[str] = Field(default_factory=list, description="추천사항")
    
    class Config:
        from_attributes = True


class InterestRecommendationResponse(BaseModel):
    """관심사 추천 응답 스키마"""
    user_id: str
    recommended_interests: List[str] = Field(..., description="추천 관심사")
    recommended_activities: List[str] = Field(default_factory=list, description="추천 활동")
    recommended_topics: List[str] = Field(default_factory=list, description="추천 주제")
    confidence_scores: Dict[str, float] = Field(default_factory=dict, description="신뢰도 점수")
    reasoning: Dict[str, str] = Field(default_factory=dict, description="추천 이유")
    related_content: List[Dict[str, Any]] = Field(default_factory=list, description="관련 콘텐츠")
    generated_at: datetime = Field(default_factory=datetime.now, description="생성 시간")
    
    class Config:
        from_attributes = True


class InterestStatsResponse(BaseModel):
    """관심사 통계 응답 스키마"""
    user_id: str
    stats_period: Dict[str, datetime] = Field(..., description="통계 기간")
    total_interests: int = Field(..., description="총 관심사 수")
    interests_by_category: Dict[str, int] = Field(..., description="카테고리별 관심사 수")
    most_mentioned_interests: List[str] = Field(..., description="가장 많이 언급된 관심사")
    recent_interest_trends: List[str] = Field(default_factory=list, description="최근 관심사 트렌드")
    engagement_score: float = Field(..., description="참여도 점수")
    diversity_score: float = Field(..., description="다양성 점수")
    activity_pattern: Dict[str, Any] = Field(default_factory=dict, description="활동 패턴")
    
    class Config:
        from_attributes = True


class InterestLogCreate(BaseModel):
    """관심사 로그 생성 스키마"""
    user_id: str = Field(..., description="사용자 ID")
    interest_id: Optional[str] = Field(None, description="관심사 ID")
    category: InterestCategoryEnum = Field(..., description="관심사 카테고리")
    keyword: str = Field(..., min_length=1, max_length=50, description="감지된 키워드")
    context: Optional[str] = Field(None, max_length=500, description="언급 맥락")
    detection_method: str = Field("keyword", description="감지 방법")
    confidence: float = Field(1.0, ge=0.0, le=1.0, description="신뢰도")
    
    @validator('keyword')
    def validate_keyword(cls, v):
        return v.strip().lower()
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "user-uuid-here",
                "category": "health",
                "keyword": "운동",
                "context": "매일 아침 운동을 하고 있어요",
                "detection_method": "keyword",
                "confidence": 0.9
            }
        } 