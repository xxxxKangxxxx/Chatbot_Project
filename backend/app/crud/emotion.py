"""
감정 관련 CRUD 연산
=====================================================

감정 기록, 분석, 요약 등의 데이터베이스 연산을 처리합니다.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy import and_, or_, func, desc, asc, case
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timedelta, date

from app.models.emotion import Emotion, EmotionSummary
from app.schemas.emotion import (
    EmotionCreate, EmotionUpdate, EmotionSummaryCreate,
    EmotionHistoryRequest, EmotionTypeEnum, EmotionIntensityEnum,
    DetectionMethodEnum
)


async def create_emotion(db: AsyncSession, emotion: EmotionCreate) -> Emotion:
    """새 감정 기록 생성"""
    emotion_data = emotion.dict()
    new_emotion = Emotion(**emotion_data)
    
    db.add(new_emotion)
    await db.commit()
    await db.refresh(new_emotion)
    return new_emotion


async def create_emotion_summary(db: AsyncSession, summary: EmotionSummaryCreate) -> EmotionSummary:
    """감정 요약 생성"""
    summary_data = summary.dict()
    new_summary = EmotionSummary(**summary_data)
    
    db.add(new_summary)
    await db.commit()
    await db.refresh(new_summary)
    return new_summary


async def get_emotion(db: AsyncSession, emotion_id: int) -> Optional[Emotion]:
    """감정 ID로 조회"""
    result = await db.execute(
        select(Emotion).where(Emotion.id == emotion_id)
    )
    return result.scalar_one_or_none()


async def get_emotion_summary(db: AsyncSession, summary_id: int) -> Optional[EmotionSummary]:
    """감정 요약 ID로 조회"""
    result = await db.execute(
        select(EmotionSummary).where(EmotionSummary.id == summary_id)
    )
    return result.scalar_one_or_none()


async def get_user_emotions(
    db: AsyncSession,
    user_id: str,
    limit: int = 50,
    offset: int = 0
) -> List[Emotion]:
    """사용자의 감정 기록 조회"""
    result = await db.execute(
        select(Emotion)
        .where(Emotion.user_id == user_id)
        .order_by(asc(Emotion.detected_at))
        .offset(offset)
        .limit(limit)
    )
    return result.scalars().all()


async def get_emotion_history(
    db: AsyncSession,
    request: EmotionHistoryRequest
) -> Tuple[List[Emotion], int]:
    """감정 히스토리 조회"""
    query = select(Emotion).where(Emotion.user_id == request.user_id)
    count_query = select(func.count(Emotion.id)).where(Emotion.user_id == request.user_id)
    
    # 날짜 범위 필터
    if request.start_date:
        query = query.where(Emotion.detected_at >= request.start_date)
        count_query = count_query.where(Emotion.detected_at >= request.start_date)
    
    if request.end_date:
        query = query.where(Emotion.detected_at <= request.end_date)
        count_query = count_query.where(Emotion.detected_at <= request.end_date)
    
    # 감정 유형 필터
    if request.emotion_types:
        query = query.where(Emotion.emotion_type.in_(request.emotion_types))
        count_query = count_query.where(Emotion.emotion_type.in_(request.emotion_types))
    
    # 강도 필터
    if request.intensity_min:
        intensity_order = {
            EmotionIntensityEnum.VERY_LOW: 1,
            EmotionIntensityEnum.LOW: 2,
            EmotionIntensityEnum.MEDIUM: 3,
            EmotionIntensityEnum.HIGH: 4,
            EmotionIntensityEnum.VERY_HIGH: 5
        }
        min_intensity_value = intensity_order.get(request.intensity_min, 1)
        
        intensity_case = case(
            (Emotion.intensity == EmotionIntensityEnum.VERY_LOW, 1),
            (Emotion.intensity == EmotionIntensityEnum.LOW, 2),
            (Emotion.intensity == EmotionIntensityEnum.MEDIUM, 3),
            (Emotion.intensity == EmotionIntensityEnum.HIGH, 4),
            (Emotion.intensity == EmotionIntensityEnum.VERY_HIGH, 5),
            else_=1
        )
        
        query = query.where(intensity_case >= min_intensity_value)
        count_query = count_query.where(intensity_case >= min_intensity_value)
    
    # 전체 개수 조회
    total_result = await db.execute(count_query)
    total_count = total_result.scalar()
    
    # 페이지네이션
    query = query.order_by(asc(Emotion.detected_at)).offset(request.offset).limit(request.limit)
    
    result = await db.execute(query)
    emotions = result.scalars().all()
    
    return emotions, total_count


async def update_emotion(
    db: AsyncSession,
    emotion_id: int,
    emotion_update: EmotionUpdate
) -> Optional[Emotion]:
    """감정 기록 업데이트"""
    result = await db.execute(
        select(Emotion).where(Emotion.id == emotion_id)
    )
    emotion = result.scalar_one_or_none()
    
    if not emotion:
        return None
    
    update_data = emotion_update.dict(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(emotion, field, value)
    
    await db.commit()
    await db.refresh(emotion)
    return emotion


async def delete_emotion(db: AsyncSession, emotion_id: int) -> bool:
    """감정 기록 삭제"""
    result = await db.execute(
        select(Emotion).where(Emotion.id == emotion_id)
    )
    emotion = result.scalar_one_or_none()
    
    if not emotion:
        return False
    
    await db.delete(emotion)
    await db.commit()
    return True


async def get_recent_emotions(
    db: AsyncSession,
    user_id: str,
    days: int = 7,
    limit: int = 10
) -> List[Emotion]:
    """최근 감정 기록 조회"""
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    result = await db.execute(
        select(Emotion)
        .where(
            and_(
                Emotion.user_id == user_id,
                Emotion.detected_at >= cutoff_date
            )
        )
        .order_by(asc(Emotion.detected_at))
        .limit(limit)
    )
    return result.scalars().all()


async def get_dominant_emotion(
    db: AsyncSession,
    user_id: str,
    days: int = 7
) -> Optional[str]:
    """주요 감정 조회"""
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    result = await db.execute(
        select(Emotion.emotion_type, func.count(Emotion.id))
        .where(
            and_(
                Emotion.user_id == user_id,
                Emotion.created_at >= cutoff_date
            )
        )
        .group_by(Emotion.emotion_type)
        .order_by(desc(func.count(Emotion.id)))
        .limit(1)
    )
    
    emotion_data = result.fetchone()
    return emotion_data[0] if emotion_data else None


async def get_emotion_distribution(
    db: AsyncSession,
    user_id: str,
    days: int = 30
) -> Dict[str, int]:
    """감정 분포 조회"""
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    result = await db.execute(
        select(Emotion.emotion_type, func.count(Emotion.id))
        .where(
            and_(
                Emotion.user_id == user_id,
                Emotion.created_at >= cutoff_date
            )
        )
        .group_by(Emotion.emotion_type)
    )
    
    return {emotion_type: count for emotion_type, count in result.fetchall()}


async def get_average_emotion_score(
    db: AsyncSession,
    user_id: str,
    days: int = 7
) -> Optional[float]:
    """평균 감정 점수 조회"""
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    result = await db.execute(
        select(func.avg(Emotion.score))
        .where(
            and_(
                Emotion.user_id == user_id,
                Emotion.created_at >= cutoff_date
            )
        )
    )
    
    avg_score = result.scalar()
    return float(avg_score) if avg_score else None


async def get_emotion_trend(
    db: AsyncSession,
    user_id: str,
    days: int = 30
) -> List[Dict[str, Any]]:
    """감정 트렌드 조회"""
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    result = await db.execute(
        select(
            func.date(Emotion.created_at).label('date'),
            func.avg(Emotion.score).label('avg_score'),
            func.count(Emotion.id).label('count')
        )
        .where(
            and_(
                Emotion.user_id == user_id,
                Emotion.created_at >= cutoff_date
            )
        )
        .group_by(func.date(Emotion.created_at))
        .order_by(func.date(Emotion.created_at))
    )
    
    return [
        {
            "date": emotion_date,
            "avg_score": float(avg_score) if avg_score else 0,
            "count": count
        }
        for emotion_date, avg_score, count in result.fetchall()
    ]


async def get_emotion_by_time_of_day(
    db: AsyncSession,
    user_id: str,
    days: int = 30
) -> Dict[str, float]:
    """시간대별 감정 패턴 조회"""
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    result = await db.execute(
        select(
            func.extract('hour', Emotion.created_at).label('hour'),
            func.avg(Emotion.score).label('avg_score')
        )
        .where(
            and_(
                Emotion.user_id == user_id,
                Emotion.created_at >= cutoff_date
            )
        )
        .group_by('hour')
        .order_by('hour')
    )
    
    return {
        str(int(hour)): float(avg_score) if avg_score else 0
        for hour, avg_score in result.fetchall()
    }


async def get_emotion_triggers(
    db: AsyncSession,
    user_id: str,
    days: int = 30
) -> Dict[str, int]:
    """감정 트리거 빈도 조회"""
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    # 트리거 배열을 개별 항목으로 분해하여 집계
    result = await db.execute(
        select(Emotion.triggers)
        .where(
            and_(
                Emotion.user_id == user_id,
                Emotion.created_at >= cutoff_date,
                Emotion.triggers.is_not(None)
            )
        )
    )
    
    trigger_count = {}
    for (triggers,) in result.fetchall():
        if triggers:
            for trigger in triggers:
                trigger_count[trigger] = trigger_count.get(trigger, 0) + 1
    
    return trigger_count


async def create_daily_emotion_summary(
    db: AsyncSession,
    user_id: str,
    target_date: date
) -> Optional[EmotionSummary]:
    """일별 감정 요약 생성"""
    start_date = datetime.combine(target_date, datetime.min.time())
    end_date = start_date + timedelta(days=1)
    
    # 해당 날짜의 감정 데이터 조회
    result = await db.execute(
        select(Emotion)
        .where(
            and_(
                Emotion.user_id == user_id,
                Emotion.created_at >= start_date,
                Emotion.created_at < end_date
            )
        )
    )
    emotions = result.scalars().all()
    
    if not emotions:
        return None
    
    # 통계 계산
    emotion_counts = {}
    total_score = 0
    
    for emotion in emotions:
        emotion_type = emotion.emotion_type.value
        emotion_counts[emotion_type] = emotion_counts.get(emotion_type, 0) + 1
        total_score += emotion.score
    
    # 주요 감정 찾기
    dominant_emotion = max(emotion_counts.items(), key=lambda x: x[1])[0]
    avg_score = total_score / len(emotions)
    
    # 기분 변화 추세 계산
    if len(emotions) > 1:
        first_half_avg = sum(e.score for e in emotions[:len(emotions)//2]) / (len(emotions)//2)
        second_half_avg = sum(e.score for e in emotions[len(emotions)//2:]) / (len(emotions) - len(emotions)//2)
        
        if second_half_avg > first_half_avg + 0.2:
            mood_trend = "improving"
        elif second_half_avg < first_half_avg - 0.2:
            mood_trend = "declining"
        else:
            mood_trend = "stable"
    else:
        mood_trend = "stable"
    
    # 기존 요약이 있는지 확인
    existing_summary_result = await db.execute(
        select(EmotionSummary)
        .where(
            and_(
                EmotionSummary.user_id == user_id,
                EmotionSummary.date == start_date
            )
        )
    )
    existing_summary = existing_summary_result.scalar_one_or_none()
    
    if existing_summary:
        # 기존 요약 업데이트
        existing_summary.dominant_emotion = EmotionTypeEnum(dominant_emotion)
        existing_summary.avg_score = avg_score
        existing_summary.emotion_count = len(emotions)
        existing_summary.emotion_distribution = emotion_counts
        existing_summary.mood_trend = mood_trend
        
        await db.commit()
        await db.refresh(existing_summary)
        return existing_summary
    else:
        # 새 요약 생성
        summary_data = EmotionSummaryCreate(
            user_id=user_id,
            date=start_date,
            dominant_emotion=EmotionTypeEnum(dominant_emotion),
            avg_score=avg_score,
            emotion_count=len(emotions),
            emotion_distribution=emotion_counts,
            mood_trend=mood_trend
        )
        return await create_emotion_summary(db, summary_data)


async def get_user_emotion_summaries(
    db: AsyncSession,
    user_id: str,
    days: int = 30
) -> List[EmotionSummary]:
    """사용자 감정 요약 조회"""
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    result = await db.execute(
        select(EmotionSummary)
        .where(
            and_(
                EmotionSummary.user_id == user_id,
                EmotionSummary.date >= cutoff_date
            )
        )
        .order_by(desc(EmotionSummary.date))
    )
    return result.scalars().all()


async def analyze_emotion_patterns(
    db: AsyncSession,
    user_id: str,
    days: int = 30
) -> Dict[str, Any]:
    """감정 패턴 분석"""
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    # 기본 통계
    total_emotions_result = await db.execute(
        select(func.count(Emotion.id))
        .where(
            and_(
                Emotion.user_id == user_id,
                Emotion.created_at >= cutoff_date
            )
        )
    )
    total_emotions = total_emotions_result.scalar() or 0
    
    if total_emotions == 0:
        return {
            "total_emotions": 0,
            "avg_score": 0,
            "dominant_emotion": None,
            "emotion_distribution": {},
            "hourly_patterns": {},
            "weekly_patterns": {},
            "mood_stability": "insufficient_data"
        }
    
    # 평균 점수
    avg_score = await get_average_emotion_score(db, user_id, days)
    
    # 주요 감정
    dominant_emotion = await get_dominant_emotion(db, user_id, days)
    
    # 감정 분포
    emotion_distribution = await get_emotion_distribution(db, user_id, days)
    
    # 시간대별 패턴
    hourly_patterns = await get_emotion_by_time_of_day(db, user_id, days)
    
    # 요일별 패턴
    weekly_result = await db.execute(
        select(
            func.extract('dow', Emotion.created_at).label('day_of_week'),
            func.avg(Emotion.score).label('avg_score')
        )
        .where(
            and_(
                Emotion.user_id == user_id,
                Emotion.created_at >= cutoff_date
            )
        )
        .group_by('day_of_week')
        .order_by('day_of_week')
    )
    
    day_names = ['일', '월', '화', '수', '목', '금', '토']
    weekly_patterns = {
        day_names[int(dow)]: float(avg_score) if avg_score else 0
        for dow, avg_score in weekly_result.fetchall()
    }
    
    # 기분 안정성 계산
    score_variance_result = await db.execute(
        select(func.variance(Emotion.score))
        .where(
            and_(
                Emotion.user_id == user_id,
                Emotion.created_at >= cutoff_date
            )
        )
    )
    score_variance = score_variance_result.scalar() or 0
    
    if score_variance < 0.1:
        mood_stability = "very_stable"
    elif score_variance < 0.3:
        mood_stability = "stable"
    elif score_variance < 0.6:
        mood_stability = "moderate"
    else:
        mood_stability = "unstable"
    
    return {
        "total_emotions": total_emotions,
        "avg_score": avg_score,
        "dominant_emotion": dominant_emotion,
        "emotion_distribution": emotion_distribution,
        "hourly_patterns": hourly_patterns,
        "weekly_patterns": weekly_patterns,
        "mood_stability": mood_stability,
        "score_variance": float(score_variance)
    }


async def get_emotion_correlations(
    db: AsyncSession,
    user_id: str,
    days: int = 30
) -> Dict[str, Any]:
    """감정 상관관계 분석"""
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    # 시간대별 감정 상관관계
    time_emotion_result = await db.execute(
        select(
            func.extract('hour', Emotion.created_at).label('hour'),
            Emotion.emotion_type,
            func.count(Emotion.id).label('count')
        )
        .where(
            and_(
                Emotion.user_id == user_id,
                Emotion.created_at >= cutoff_date
            )
        )
        .group_by('hour', Emotion.emotion_type)
    )
    
    time_correlations = {}
    for hour, emotion_type, count in time_emotion_result.fetchall():
        hour_str = str(int(hour))
        if hour_str not in time_correlations:
            time_correlations[hour_str] = {}
        time_correlations[hour_str][emotion_type.value] = count
    
    # 트리거별 감정 상관관계
    trigger_correlations = await get_emotion_triggers(db, user_id, days)
    
    return {
        "time_correlations": time_correlations,
        "trigger_correlations": trigger_correlations
    }


async def get_emotion_statistics(db: AsyncSession) -> Dict[str, Any]:
    """전체 감정 통계"""
    # 총 감정 기록 수
    total_emotions_result = await db.execute(
        select(func.count(Emotion.id))
    )
    total_emotions = total_emotions_result.scalar() or 0
    
    # 감정 유형별 분포
    emotion_distribution_result = await db.execute(
        select(Emotion.emotion_type, func.count(Emotion.id))
        .group_by(Emotion.emotion_type)
        .order_by(desc(func.count(Emotion.id)))
    )
    emotion_distribution = {
        emotion_type.value: count for emotion_type, count in emotion_distribution_result.fetchall()
    }
    
    # 평균 감정 점수
    avg_score_result = await db.execute(
        select(func.avg(Emotion.score))
    )
    avg_score = avg_score_result.scalar() or 0
    
    # 감지 방법별 분포
    detection_method_result = await db.execute(
        select(Emotion.detection_method, func.count(Emotion.id))
        .group_by(Emotion.detection_method)
    )
    detection_methods = {
        method.value: count for method, count in detection_method_result.fetchall()
    }
    
    return {
        "total_emotions": total_emotions,
        "emotion_distribution": emotion_distribution,
        "avg_score": float(avg_score),
        "detection_methods": detection_methods
    }


async def bulk_create_emotions(
    db: AsyncSession,
    emotions: List[EmotionCreate]
) -> List[Emotion]:
    """감정 일괄 생성"""
    emotion_objects = [Emotion(**emotion.dict()) for emotion in emotions]
    
    db.add_all(emotion_objects)
    await db.commit()
    
    for emotion in emotion_objects:
        await db.refresh(emotion)
    
    return emotion_objects


async def delete_old_emotions(
    db: AsyncSession,
    days: int = 365
) -> int:
    """오래된 감정 기록 삭제"""
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    result = await db.execute(
        select(Emotion).where(Emotion.created_at < cutoff_date)
    )
    emotions_to_delete = result.scalars().all()
    
    count = len(emotions_to_delete)
    for emotion in emotions_to_delete:
        await db.delete(emotion)
    
    await db.commit()
    return count


# 추가된 함수들 (API에서 사용하는 함수들)

async def create_emotion_record(db: AsyncSession, emotion_data: dict) -> Emotion:
    """감정 기록 생성 (딕셔너리 데이터 입력)"""
    import uuid
    
    # UUID 생성
    emotion_data['id'] = str(uuid.uuid4())
    new_emotion = Emotion(**emotion_data)
    
    db.add(new_emotion)
    await db.commit()
    await db.refresh(new_emotion)
    return new_emotion


async def get_user_recent_emotions(
    db: AsyncSession,
    user_id: str,
    days_back: int = 7
) -> List[Emotion]:
    """사용자의 최근 감정 기록 조회 (문자열 user_id 지원)"""
    cutoff_date = datetime.utcnow() - timedelta(days=days_back)
    
    query = select(Emotion).where(
        and_(
            Emotion.user_id == user_id,
            Emotion.detected_at >= cutoff_date
        )
    ).order_by(desc(Emotion.detected_at))
    
    result = await db.execute(query)
    return result.scalars().all() 


async def get_emotion_statistics_for_user(
    db: AsyncSession,
    user_id: str,
    days_back: int = 30
) -> Dict[str, Any]:
    """사용자의 감정 통계 집계"""
    cutoff_date = datetime.utcnow() - timedelta(days=days_back)
    
    # 기본 감정 데이터 조회
    emotions_query = select(Emotion).where(
        and_(
            Emotion.user_id == user_id,
            Emotion.detected_at >= cutoff_date
        )
    )
    
    result = await db.execute(emotions_query)
    emotions = result.scalars().all()
    
    if not emotions:
        return {
            "total_emotions": 0,
            "emotion_distribution": {},
            "avg_intensity": 0.0,
            "dominant_emotion": "neutral",
            "emotion_frequency": {},
            "mood_stability": 0.5,
            "positive_ratio": 0.5,
            "emotional_range": 0.0,
            "recent_emotions": []
        }
    
    # 감정 분포 계산
    emotion_counts = {}
    emotion_intensities = {}
    positive_emotions = ["기쁨", "행복", "만족", "편안", "희망", "감사"]
    negative_emotions = ["우울", "슬픔", "화남", "불안", "걱정", "외로움"]
    
    positive_count = 0
    negative_count = 0
    neutral_count = 0
    total_intensity = 0
    
    for emotion in emotions:
        # 감정별 개수
        emotion_counts[emotion.emotion] = emotion_counts.get(emotion.emotion, 0) + 1
        
        # 감정별 강도 합계
        if emotion.emotion not in emotion_intensities:
            emotion_intensities[emotion.emotion] = []
        emotion_intensities[emotion.emotion].append(emotion.intensity)
        
        # 긍정/부정/중립 분류
        if emotion.emotion in positive_emotions:
            positive_count += 1
        elif emotion.emotion in negative_emotions:
            negative_count += 1
        else:
            neutral_count += 1
        
        total_intensity += emotion.intensity
    
    # 지배적 감정
    dominant_emotion = max(emotion_counts.keys(), key=lambda k: emotion_counts[k]) if emotion_counts else "neutral"
    
    # 평균 강도
    avg_intensity = total_intensity / len(emotions) if emotions else 0.0
    
    # 긍정 비율
    total_emotions = len(emotions)
    positive_ratio = positive_count / total_emotions if total_emotions > 0 else 0.5
    
    # 감정 안정성 (강도 변화의 표준편차)
    intensities = [e.intensity for e in emotions]
    if len(intensities) > 1:
        import statistics
        intensity_std = statistics.stdev(intensities)
        mood_stability = max(0.0, 1.0 - intensity_std)  # 표준편차가 작을수록 안정적
    else:
        mood_stability = 0.5
    
    # 감정 범위 (최대 강도 - 최소 강도)
    emotional_range = max(intensities) - min(intensities) if intensities else 0.0
    
    # 최근 감정 (최근 5개)
    recent_emotions = []
    for emotion in sorted(emotions, key=lambda x: x.detected_at, reverse=True)[:5]:
        recent_emotions.append({
            "emotion": emotion.emotion,
            "intensity": emotion.intensity,
            "detected_at": emotion.detected_at.isoformat() if emotion.detected_at else None,
            "context": emotion.context
        })
    
    # 감정별 평균 강도
    emotion_avg_intensities = {}
    for emotion_type, intensities_list in emotion_intensities.items():
        emotion_avg_intensities[emotion_type] = sum(intensities_list) / len(intensities_list)
    
    return {
        "total_emotions": total_emotions,
        "emotion_distribution": emotion_counts,
        "avg_intensity": round(avg_intensity, 2),
        "dominant_emotion": dominant_emotion,
        "emotion_frequency": emotion_counts,
        "emotion_avg_intensities": emotion_avg_intensities,
        "mood_stability": round(mood_stability, 2),
        "positive_ratio": round(positive_ratio, 2),
        "emotional_range": round(emotional_range, 2),
        "recent_emotions": recent_emotions,
        "positive_count": positive_count,
        "negative_count": negative_count,
        "neutral_count": neutral_count
    } 