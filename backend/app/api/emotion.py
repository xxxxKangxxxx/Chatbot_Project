"""
감정 API 라우터

사용자의 감정 데이터 조회, 분석, 트렌드 등의 기능을 제공합니다.
"""

from typing import List, Optional
import logging
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
import uuid

from app.database import get_db
from app.schemas.emotion import (
    EmotionResponse, EmotionTrendAnalysis, EmotionSummaryResponse,
    EmotionAnalysisRequest, EmotionStatsResponse, EmotionPatternResponse
)
from app.crud.user import get_user_by_id
from app.crud.emotion import (
    get_user_emotions, get_emotion, get_user_recent_emotions,
    create_emotion, update_emotion, delete_emotion,
    get_emotion_statistics_for_user
)
from app.crud.chat_log import get_user_chat_history
from app.models.emotion import Emotion
from app.services import (
    analyze_text_emotion, get_emotion_trend, detect_emotion_patterns
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/emotions", tags=["emotions"])

@router.get("/{user_id}")
async def get_user_emotions_endpoint(
    user_id: str,
    start_date: Optional[datetime] = Query(None, description="조회 시작 날짜"),
    end_date: Optional[datetime] = Query(None, description="조회 종료 날짜"),
    emotion_type: Optional[str] = Query(None, description="특정 감정 타입 필터"),
    limit: int = Query(100, ge=1, le=1000, description="조회할 최대 개수"),
    offset: int = Query(0, ge=0, description="조회 시작 위치"),
    db: AsyncSession = Depends(get_db)
):
    """
    사용자의 감정 기록 조회
    """
    try:
        # 사용자 존재 확인
        user = await get_user_by_id(db, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")
        
        # 기본 날짜 범위 설정 (지정되지 않은 경우 최근 30일)
        if not end_date:
            end_date = datetime.now()
        if not start_date:
            start_date = end_date - timedelta(days=30)
        
        # 감정 기록 조회
        emotions = await get_user_emotions(
            db, user_id, limit, offset
        )
        
        # 응답 형식 변환 (임시로 딕셔너리로 반환)
        emotion_responses = []
        for emotion in emotions:
            emotion_responses.append({
                "id": emotion.id,
                "user_id": emotion.user_id,
                "emotion": emotion.emotion,
                "intensity": emotion.intensity,
                "context": emotion.context,
                "detected_method": emotion.detected_method,
                "detected_at": emotion.detected_at.isoformat() if emotion.detected_at else None
            })
        
        return emotion_responses
        
    except Exception as e:
        logger.error(f"감정 기록 조회 중 오류 발생: {str(e)}")
        raise HTTPException(status_code=500, detail=f"감정 기록 조회 중 오류가 발생했습니다: {str(e)}")

@router.get("/{user_id}/trends")
async def get_emotion_trends_endpoint(
    user_id: str,
    days_back: int = Query(30, ge=1, le=365, description="분석할 과거 일수"),
    db: AsyncSession = Depends(get_db)
):
    """
    사용자의 감정 트렌드 분석
    """
    try:
        # 사용자 존재 확인
        user = await get_user_by_id(db, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")
        
        # 실제 감정 통계 집계
        stats = await get_emotion_statistics_for_user(db, user_id, days_back)
        
        # 트렌드 분석 데이터 구성
        trend_data = {
            "user_id": user_id,
            "period_start": (datetime.now() - timedelta(days=days_back)).isoformat(),
            "period_end": datetime.now().isoformat(),
            "total_entries": stats["total_emotions"],
            "avg_score": stats["avg_intensity"],
            "score_trend": "stable" if stats["mood_stability"] > 0.7 else "fluctuating",
            "emotion_distribution": stats["emotion_distribution"],
            "intensity_distribution": stats["emotion_avg_intensities"],
            "mood_stability": stats["mood_stability"],
            "positive_ratio": stats["positive_ratio"],
            "emotional_range": stats["emotional_range"],
            "recent_emotions": stats["recent_emotions"],
            "message": "트렌드 분석 완료"
        }
        
        return trend_data
        
    except Exception as e:
        logger.error(f"감정 트렌드 분석 중 오류 발생: {str(e)}")
        raise HTTPException(status_code=500, detail=f"감정 트렌드 분석 중 오류가 발생했습니다: {str(e)}")

@router.get("/{user_id}/summary")
async def get_emotion_summary(
    user_id: str,
    date: Optional[datetime] = Query(None, description="요약할 날짜 (기본값: 오늘)"),
    db: AsyncSession = Depends(get_db)
):
    """
    특정 날짜의 감정 요약 조회
    """
    try:
        # 사용자 존재 확인
        user = await get_user_by_id(db, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")
        
        # 기본 날짜 설정
        if not date:
            date = datetime.now().date()
        elif isinstance(date, datetime):
            date = date.date()
        
        # 해당 날짜의 감정 데이터 조회
        start_datetime = datetime.combine(date, datetime.min.time())
        end_datetime = datetime.combine(date, datetime.max.time())
        
        # 해당 날짜의 감정 기록만 조회
        emotions_query = select(Emotion).where(
            and_(
                Emotion.user_id == user_id,
                Emotion.detected_at >= start_datetime,
                Emotion.detected_at <= end_datetime
            )
        )
        
        result = await db.execute(emotions_query)
        emotions = result.scalars().all()
        
        if emotions:
            # 감정 분포 계산
            emotion_counts = {}
            total_intensity = 0
            
            for emotion in emotions:
                emotion_type = emotion.emotion
                emotion_counts[emotion_type] = emotion_counts.get(emotion_type, 0) + 1
                total_intensity += emotion.intensity
            
            # 지배적 감정과 평균 강도 계산
            dominant_emotion = max(emotion_counts.keys(), key=lambda k: emotion_counts[k])
            avg_intensity = total_intensity / len(emotions)
            
            return {
                "user_id": user_id,
                "date": date.isoformat() if hasattr(date, 'isoformat') else str(date),
                "dominant_emotion": dominant_emotion,
                "avg_intensity": round(avg_intensity, 2),
                "emotion_distribution": emotion_counts,
                "total_records": len(emotions),
                "summary_type": "generated"
            }
        else:
            return {
                "user_id": user_id,
                "date": date.isoformat() if hasattr(date, 'isoformat') else str(date),
                "dominant_emotion": "neutral",
                "avg_intensity": 0.5,
                "emotion_distribution": {},
                "total_records": 0,
                "summary_type": "empty"
            }
        
        return EmotionSummaryResponse(
            id=summary.id,
            user_id=summary.user_id,
            date=summary.date,
            dominant_emotion=summary.dominant_emotion,
            avg_intensity=summary.avg_intensity,
            emotion_distribution=summary.emotion_distribution,
            total_records=summary.total_records,
            notes=summary.notes,
            created_at=summary.created_at
        )
        
    except Exception as e:
        logger.error(f"감정 요약 조회 중 오류 발생: {str(e)}")
        raise HTTPException(status_code=500, detail=f"감정 요약 조회 중 오류가 발생했습니다: {str(e)}")

@router.get("/{user_id}/stats")
async def get_emotion_statistics(
    user_id: str,
    days_back: int = Query(30, ge=1, le=365, description="통계 기간 (일)"),
    db: AsyncSession = Depends(get_db)
):
    """
    사용자의 감정 통계 조회
    """
    try:
        # 사용자 존재 확인
        user = await get_user_by_id(db, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")
        
        # 실제 감정 통계 집계
        stats = await get_emotion_statistics_for_user(db, user_id, days_back)
        
        # 응답 데이터 구성
        response_data = {
            "user_id": user_id,
            "stats_period": {
                "start": (datetime.now() - timedelta(days=days_back)).isoformat(),
                "end": datetime.now().isoformat()
            },
            **stats
        }
        
        return response_data
        
    except Exception as e:
        logger.error(f"감정 통계 조회 중 오류 발생: {str(e)}")
        raise HTTPException(status_code=500, detail=f"감정 통계 조회 중 오류가 발생했습니다: {str(e)}")

@router.get("/{user_id}/patterns", response_model=EmotionPatternResponse)
async def get_emotion_patterns(
    user_id: str,
    days_back: int = Query(60, ge=7, le=365, description="패턴 분석 기간 (일)"),
    db: AsyncSession = Depends(get_db)
):
    """
    사용자의 감정 패턴 분석
    """
    try:
        # 사용자 존재 확인
        user = await get_user_by_id(db, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")
        
        # 감정 기록 조회
        emotions = await get_user_emotions(db, user_id, 1000, 0)
        
        # 감정 데이터를 딕셔너리 형태로 변환
        emotions_data = []
        for emotion in emotions:
            emotions_data.append({
                'emotion': emotion.emotion,
                'intensity': emotion.intensity,
                'timestamp': emotion.detected_at
            })
        
        # 패턴 분석 실행
        patterns = await detect_emotion_patterns(user_id, emotions_data)
        
        return EmotionPatternResponse(
            user_id=user_id,
            analysis_period_days=days_back,
            time_patterns=patterns.get('time_patterns', {}),
            transition_patterns=patterns.get('transition_patterns', {}),
            cyclical_patterns=patterns.get('cyclical_patterns', {}),
            anomalies=patterns.get('anomalies', []),
            pattern_insights=patterns.get('insights', []),
            confidence_score=patterns.get('confidence_score', 0.0),
            analyzed_records=len(emotions_data)
        )
        
    except Exception as e:
        logger.error(f"감정 패턴 분석 중 오류 발생: {str(e)}")
        raise HTTPException(status_code=500, detail=f"감정 패턴 분석 중 오류가 발생했습니다: {str(e)}")

@router.post("/{user_id}/analyze")
async def analyze_text_emotion_endpoint(
    user_id: str,
    request: EmotionAnalysisRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    텍스트 감정 분석 (실시간)
    """
    try:
        # 사용자 존재 확인
        user = await get_user_by_id(db, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")
        
        # 감정 분석 실행
        emotion_result = await analyze_text_emotion(request.text, user_id)
        
        # 감정 분석 결과 DB 저장
        if getattr(request, "save_to_history", True):
            from app.models.emotion import Emotion
            emotion_obj = Emotion(
                id=str(uuid.uuid4()),
                user_id=user_id,
                emotion=emotion_result.primary_emotion.value,
                intensity=emotion_result.intensity,
                context=request.text,
                detected_method=emotion_result.analysis_method,
                detected_at=emotion_result.timestamp
            )
            db.add(emotion_obj)
            await db.commit()
        
        return {
            "user_id": user_id,
            "analyzed_text": request.text,
            "analysis_result": {
                "primary_emotion": emotion_result.primary_emotion.value,
                "emotion_scores": emotion_result.emotion_scores if hasattr(emotion_result, 'emotion_scores') else {},
                "intensity": emotion_result.intensity,
                "confidence": emotion_result.confidence,
                "detected_keywords": emotion_result.detected_keywords,
                "analysis_method": emotion_result.analysis_method
            },
            "analysis_timestamp": emotion_result.timestamp,
            "save_to_history": getattr(request, "save_to_history", True)
        }
        
    except Exception as e:
        logger.error(f"텍스트 감정 분석 중 오류 발생: {str(e)}")
        raise HTTPException(status_code=500, detail=f"텍스트 감정 분석 중 오류가 발생했습니다: {str(e)}")

@router.get("/{user_id}/recent")
async def get_recent_emotions(
    user_id: str,
    days_back: int = Query(7, ge=1, le=30, description="조회할 과거 일수"),
    limit: int = Query(20, ge=1, le=100, description="조회할 최대 개수"),
    db: AsyncSession = Depends(get_db)
):
    """
    최근 감정 기록 조회
    """
    try:
        # 사용자 존재 확인
        user = await get_user_by_id(db, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")
        
        # 최근 감정 기록 조회
        emotions = await get_user_recent_emotions(db, user_id, days_back)
        
        # 응답 형식 변환
        emotion_responses = []
        for emotion in emotions:
            emotion_responses.append({
                "id": emotion.id,
                "emotion": emotion.emotion,
                "intensity": emotion.intensity,
                "context": emotion.context,
                "detected_method": emotion.detected_method,
                "detected_at": emotion.detected_at.isoformat() if emotion.detected_at else None,
                "time_ago": str(datetime.now() - emotion.detected_at) if emotion.detected_at else "Unknown"
            })
        
        return {
            "user_id": user_id,
            "period_days": days_back,
            "emotions": emotion_responses,
            "total_count": len(emotion_responses)
        }
        
    except Exception as e:
        logger.error(f"최근 감정 조회 중 오류 발생: {str(e)}")
        raise HTTPException(status_code=500, detail=f"최근 감정 조회 중 오류가 발생했습니다: {str(e)}")

@router.get("/{user_id}/daily")
async def get_daily_emotion_summary(
    user_id: str,
    start_date: Optional[datetime] = Query(None, description="시작 날짜"),
    end_date: Optional[datetime] = Query(None, description="종료 날짜"),
    db: AsyncSession = Depends(get_db)
):
    """
    일별 감정 요약 조회
    """
    try:
        # 사용자 존재 확인
        user = await get_user_by_id(db, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")
        
        # 기본 날짜 범위 설정
        if not end_date:
            end_date = datetime.now()
        if not start_date:
            start_date = end_date - timedelta(days=7)
        
        # 전체 감정 기록 조회 (날짜 필터링 없이)
        all_emotions = await get_user_emotions(db, user_id, 1000, 0)
        
        # 일별 요약 생성
        daily_summaries = []
        current_date = start_date.date()
        end_date_only = end_date.date()
        
        while current_date <= end_date_only:
            start_datetime = datetime.combine(current_date, datetime.min.time())
            end_datetime = datetime.combine(current_date, datetime.max.time())
            
            # 해당 날짜의 감정 기록 필터링
            day_emotions = [
                emotion for emotion in all_emotions 
                if emotion.detected_at and start_datetime <= emotion.detected_at <= end_datetime
            ]
            
            if day_emotions:
                # 감정 분포 계산
                emotion_counts = {}
                total_intensity = 0
                
                for emotion in day_emotions:
                    emotion_type = emotion.emotion
                    emotion_counts[emotion_type] = emotion_counts.get(emotion_type, 0) + 1
                    total_intensity += emotion.intensity
                
                dominant_emotion = max(emotion_counts.keys(), key=lambda k: emotion_counts[k])
                avg_intensity = total_intensity / len(day_emotions)
                
                daily_summaries.append({
                    "date": current_date,
                    "dominant_emotion": dominant_emotion,
                    "avg_intensity": round(avg_intensity, 2),
                    "emotion_distribution": emotion_counts,
                    "total_records": len(day_emotions)
                })
            else:
                daily_summaries.append({
                    "date": current_date,
                    "dominant_emotion": "neutral",
                    "avg_intensity": 0.5,
                    "emotion_distribution": {},
                    "total_records": 0
                })
            
            current_date += timedelta(days=1)
        
        return {
            "user_id": user_id,
            "start_date": start_date.date(),
            "end_date": end_date.date(),
            "daily_summaries": daily_summaries,
            "total_days": len(daily_summaries)
        }
        
    except Exception as e:
        logger.error(f"일별 감정 요약 조회 중 오류 발생: {str(e)}")
        raise HTTPException(status_code=500, detail=f"일별 감정 요약 조회 중 오류가 발생했습니다: {str(e)}")

@router.delete("/{emotion_id}")
async def delete_emotion_record_endpoint(
    emotion_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    감정 기록 삭제
    """
    try:
        # 감정 기록 존재 확인
        emotion = await get_emotion_by_id(db, emotion_id)
        if not emotion:
            raise HTTPException(status_code=404, detail="감정 기록을 찾을 수 없습니다")
        
        # 감정 기록 삭제
        success = await delete_emotion_record(db, emotion_id)
        if not success:
            raise HTTPException(status_code=500, detail="감정 기록 삭제에 실패했습니다")
        
        logger.info(f"감정 기록 삭제 완료 - ID: {emotion_id}")
        
        return {"message": "감정 기록이 성공적으로 삭제되었습니다", "emotion_id": emotion_id}
        
    except Exception as e:
        logger.error(f"감정 기록 삭제 중 오류 발생: {str(e)}")
        raise HTTPException(status_code=500, detail=f"감정 기록 삭제 중 오류가 발생했습니다: {str(e)}")

@router.get("/{user_id}/insights")
async def get_emotion_insights(
    user_id: str,
    days_back: int = Query(30, ge=7, le=90, description="인사이트 분석 기간 (일)"),
    db: AsyncSession = Depends(get_db)
):
    """
    사용자 감정 인사이트 조회
    """
    try:
        # 사용자 존재 확인
        user = await get_user_by_id(db, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")
        
        # 감정 기록 및 채팅 기록 조회
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        emotions = await get_user_emotions(db, user_id, start_date, end_date)
        chats = await get_user_chat_history(db, user_id, limit=200)
        
        # 데이터 변환
        emotions_data = [{'emotion': e.emotion, 'intensity': e.intensity, 'timestamp': e.timestamp} for e in emotions]
        
        # 트렌드 및 패턴 분석
        trend_analysis = await get_emotion_trend(user_id, emotions_data, days_back)
        patterns = await detect_emotion_patterns(user_id, emotions_data)
        
        # 인사이트 생성
        insights = []
        
        # 트렌드 기반 인사이트
        if trend_analysis.trend_direction == "improving":
            insights.append("감정 상태가 점차 개선되고 있는 긍정적인 추세를 보이고 있습니다.")
        elif trend_analysis.trend_direction == "declining":
            insights.append("감정 상태가 다소 악화되고 있어 관심과 지원이 필요합니다.")
        
        # 지배적 감정 기반 인사이트
        if trend_analysis.dominant_emotion.value == "lonely":
            insights.append("외로움을 자주 느끼고 계시는 것 같습니다. 사회적 연결을 늘려보시는 것이 도움이 될 수 있습니다.")
        elif trend_analysis.dominant_emotion.value == "happy":
            insights.append("전반적으로 긍정적인 감정을 많이 경험하고 계십니다.")
        
        # 패턴 기반 인사이트
        if patterns.get('anomalies'):
            insights.append("특정 감정이 과도하게 나타나는 패턴이 발견되었습니다.")
        
        # 활동 기반 인사이트
        if len(chats) > 50:
            insights.append("활발한 대화 활동을 통해 감정 표현을 잘 하고 계십니다.")
        
        return {
            "user_id": user_id,
            "analysis_period": days_back,
            "insights": insights,
            "trend_summary": {
                "direction": trend_analysis.trend_direction,
                "dominant_emotion": trend_analysis.dominant_emotion.value,
                "average_intensity": trend_analysis.average_intensity
            },
            "pattern_summary": {
                "has_patterns": len(patterns.get('time_patterns', {})) > 0,
                "anomaly_count": len(patterns.get('anomalies', [])),
                "confidence": patterns.get('confidence_score', 0.0)
            },
            "data_quality": {
                "emotion_records": len(emotions),
                "chat_messages": len(chats),
                "analysis_confidence": "high" if len(emotions) > 30 else "medium" if len(emotions) > 10 else "low"
            },
            "generated_at": datetime.now()
        }
        
    except Exception as e:
        logger.error(f"감정 인사이트 조회 중 오류 발생: {str(e)}")
        raise HTTPException(status_code=500, detail=f"감정 인사이트 조회 중 오류가 발생했습니다: {str(e)}") 