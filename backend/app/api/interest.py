"""
관심사 API 라우터

사용자의 관심사 관리, 분석, 추천 등의 기능을 제공합니다.
"""

from typing import List, Optional, Dict, Any
import logging
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.interest import (
    InterestCreate, InterestResponse, InterestUpdate, InterestAnalysisResponse,
    InterestRecommendationResponse, InterestTrendResponse, InterestStatsResponse
)
from app.crud.user import get_user_by_id
from app.crud.interest import (
    create_interest, get_interest, get_user_interests, update_interest,
    delete_interest, analyze_user_interests
)
from app.crud.chat_log import get_user_chat_history
from app.crud.emotion import get_user_recent_emotions
from app.services import analyze_user_profile, get_personalized_recommendations

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/interests", tags=["interests"])

# 관심사 기본 관리

@router.post("/")
async def create_interest_endpoint(
    interest_data: InterestCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    새로운 관심사 생성
    """
    try:
        # 사용자 존재 확인
        user = await get_user_by_id(db, interest_data.user_id)
        if not user:
            raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")
        
        # 관심사 생성
        new_interest = await create_interest(db, interest_data)
        
        logger.info(f"관심사 생성 완료 - 사용자: {interest_data.user_id}, 카테고리: {interest_data.category}")
        
        # 딕셔너리 응답으로 변환
        return {
            "id": new_interest.id,
            "user_id": new_interest.user_id,
            "keyword": new_interest.keyword,
            "category": new_interest.category,
            "weight": new_interest.weight,
            "mentioned_count": new_interest.mentioned_count,
            "last_mentioned": new_interest.last_mentioned,
            "is_active": new_interest.is_active,
            "created_at": new_interest.created_at
        }
        
    except Exception as e:
        logger.error(f"관심사 생성 중 오류 발생: {str(e)}")
        raise HTTPException(status_code=500, detail=f"관심사 생성 중 오류가 발생했습니다: {str(e)}")

@router.get("/{interest_id}")
async def get_interest_endpoint(
    interest_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    관심사 조회
    """
    try:
        interest = await get_interest(db, interest_id)
        if not interest:
            raise HTTPException(status_code=404, detail="관심사를 찾을 수 없습니다")
        
        # 딕셔너리 응답으로 변환
        return {
            "id": interest.id,
            "user_id": interest.user_id,
            "keyword": interest.keyword,
            "category": interest.category,
            "weight": interest.weight,
            "mentioned_count": interest.mentioned_count,
            "last_mentioned": interest.last_mentioned,
            "is_active": interest.is_active,
            "created_at": interest.created_at
        }
        
    except Exception as e:
        logger.error(f"관심사 조회 중 오류 발생: {str(e)}")
        raise HTTPException(status_code=500, detail=f"관심사 조회 중 오류가 발생했습니다: {str(e)}")

@router.get("/user/{user_id}")
async def get_user_interests_endpoint(
    user_id: str,
    category: Optional[str] = Query(None, description="특정 카테고리 필터"),
    min_interest_level: Optional[int] = Query(None, ge=1, le=10, description="최소 관심도 수준"),
    db: AsyncSession = Depends(get_db)
):
    """
    사용자의 관심사 목록 조회
    """
    try:
        # 사용자 존재 확인
        user = await get_user_by_id(db, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")
        
        # 관심사 목록 조회
        interests = await get_user_interests(db, user_id)
        
        # 딕셔너리 응답으로 변환
        result = []
        for interest in interests:
            interest_dict = {
                "id": interest.id,
                "user_id": interest.user_id,
                "keyword": interest.keyword,
                "category": interest.category,
                "weight": interest.weight,
                "mentioned_count": interest.mentioned_count,
                "last_mentioned": interest.last_mentioned,
                "is_active": interest.is_active,
                "created_at": interest.created_at
            }
            result.append(interest_dict)
        
        return result
        
    except Exception as e:
        logger.error(f"사용자 관심사 조회 중 오류 발생: {str(e)}")
        raise HTTPException(status_code=500, detail=f"사용자 관심사 조회 중 오류가 발생했습니다: {str(e)}")

@router.put("/{interest_id}")
async def update_interest_endpoint(
    interest_id: str,
    interest_data: InterestUpdate,
    db: AsyncSession = Depends(get_db)
):
    """
    관심사 수정
    """
    try:
        # 관심사 존재 확인
        existing_interest = await get_interest(db, interest_id)
        if not existing_interest:
            raise HTTPException(status_code=404, detail="관심사를 찾을 수 없습니다")
        
        # 관심사 업데이트
        updated_interest = await update_interest(db, interest_id, interest_data)
        if not updated_interest:
            raise HTTPException(status_code=500, detail="관심사 업데이트에 실패했습니다")
        
        logger.info(f"관심사 업데이트 완료 - ID: {interest_id}")
        
        # 딕셔너리 응답으로 변환
        return {
            "id": updated_interest.id,
            "user_id": updated_interest.user_id,
            "keyword": updated_interest.keyword,
            "category": updated_interest.category,
            "weight": updated_interest.weight,
            "mentioned_count": updated_interest.mentioned_count,
            "last_mentioned": updated_interest.last_mentioned,
            "is_active": updated_interest.is_active,
            "created_at": updated_interest.created_at
        }
        
    except Exception as e:
        logger.error(f"관심사 수정 중 오류 발생: {str(e)}")
        raise HTTPException(status_code=500, detail=f"관심사 수정 중 오류가 발생했습니다: {str(e)}")

@router.delete("/{interest_id}")
async def delete_interest_endpoint(
    interest_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    관심사 삭제
    """
    try:
        # 관심사 존재 확인
        interest = await get_interest(db, interest_id)
        if not interest:
            raise HTTPException(status_code=404, detail="관심사를 찾을 수 없습니다")
        
        # 관심사 삭제
        success = await delete_interest(db, interest_id)
        if not success:
            raise HTTPException(status_code=500, detail="관심사 삭제에 실패했습니다")
        
        logger.info(f"관심사 삭제 완료 - ID: {interest_id}")
        
        return {"message": "관심사가 성공적으로 삭제되었습니다", "interest_id": interest_id}
        
    except Exception as e:
        logger.error(f"관심사 삭제 중 오류 발생: {str(e)}")
        raise HTTPException(status_code=500, detail=f"관심사 삭제 중 오류가 발생했습니다: {str(e)}")

# 관심사 분석 및 추천

@router.get("/analysis/{user_id}", response_model=InterestAnalysisResponse)
async def get_interest_analysis(
    user_id: str,
    days_back: int = Query(30, ge=1, le=365, description="분석 기간 (일)"),
    db: AsyncSession = Depends(get_db)
):
    """
    사용자의 관심사 분석
    """
    try:
        # 사용자 존재 확인
        user = await get_user_by_id(db, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")
        
        # 채팅 기록 조회
        recent_chats = await get_user_chat_history(db, user_id, limit=200)
        chat_history = []
        for chat in recent_chats:
            chat_history.append({
                'message': chat.message,
                'role': chat.role,
                'timestamp': chat.timestamp
            })
        
        # 감정 기록 조회
        recent_emotions = await get_user_recent_emotions(db, user_id, days_back)
        emotion_history = []
        for emotion in recent_emotions:
            emotion_history.append({
                'emotion': emotion.emotion,
                'intensity': emotion.intensity,
                'timestamp': emotion.timestamp
            })
        
        # 기존 관심사 조회
        existing_interests = await get_user_interests(db, user_id)
        
        # 프로필 분석 실행
        profile_analysis = await analyze_user_profile(
            user_id=user_id,
            chat_history=chat_history,
            emotion_history=emotion_history
        )
        
        # 관심사 분석 결과 구성
        interests_analysis = profile_analysis.get('interests', {})
        
        return InterestAnalysisResponse(
            user_id=user_id,
            analysis_period_days=days_back,
            detected_interests=interests_analysis.get('interests', {}),
            interest_confidence=interests_analysis.get('confidence', {}),
            emerging_interests=interests_analysis.get('emerging', []),
            declining_interests=interests_analysis.get('declining', []),
            stable_interests=interests_analysis.get('stable', []),
            interest_categories=interests_analysis.get('categories', {}),
            analysis_timestamp=datetime.now(),
            data_sources={
                "chat_messages": len(chat_history),
                "emotion_records": len(emotion_history),
                "existing_interests": len(existing_interests)
            }
        )
        
    except Exception as e:
        logger.error(f"관심사 분석 중 오류 발생: {str(e)}")
        raise HTTPException(status_code=500, detail=f"관심사 분석 중 오류가 발생했습니다: {str(e)}")

@router.get("/recommendations/{user_id}", response_model=InterestRecommendationResponse)
async def get_interest_recommendations(
    user_id: str,
    recommendation_type: str = Query("all", description="추천 유형 (all, activities, topics, social)"),
    db: AsyncSession = Depends(get_db)
):
    """
    사용자 맞춤 관심사 추천
    """
    try:
        # 사용자 존재 확인
        user = await get_user_by_id(db, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")
        
        # 사용자 데이터 조회
        recent_chats = await get_user_chat_history(db, user_id, limit=100)
        chat_history = [{'message': chat.message, 'role': chat.role, 'timestamp': chat.timestamp} for chat in recent_chats]
        
        recent_emotions = await get_user_recent_emotions(db, user_id, days_back=14)
        emotion_history = [{'emotion': emotion.emotion, 'intensity': emotion.intensity, 'timestamp': emotion.timestamp} for emotion in recent_emotions]
        
        # 프로필 분석
        profile_analysis = await analyze_user_profile(user_id, chat_history, emotion_history)
        
        # 개인화 추천 생성
        recommendations = await get_personalized_recommendations(
            user_id=user_id,
            interests=profile_analysis.get('interests', {}).get('interests', {}),
            personality_traits=profile_analysis.get('personality_traits', {}).get('traits', {}),
            communication_style=profile_analysis.get('communication_style', {})
        )
        
        # 추천 결과 필터링
        filtered_recommendations = recommendations.get('recommendations', {})
        if recommendation_type != "all":
            filtered_recommendations = {
                k: v for k, v in filtered_recommendations.items() 
                if recommendation_type in k.lower()
            }
        
        return InterestRecommendationResponse(
            user_id=user_id,
            recommendation_type=recommendation_type,
            recommendations=filtered_recommendations,
            personalization_score=recommendations.get('personalization_score', 0.0),
            recommendation_reasons=recommendations.get('reasons', []),
            confidence_level=recommendations.get('confidence_level', 'medium'),
            generated_at=datetime.now(),
            expires_at=datetime.now() + timedelta(days=7)
        )
        
    except Exception as e:
        logger.error(f"관심사 추천 중 오류 발생: {str(e)}")
        raise HTTPException(status_code=500, detail=f"관심사 추천 중 오류가 발생했습니다: {str(e)}")

@router.get("/trends/{user_id}", response_model=InterestTrendResponse)
async def get_interest_trends(
    user_id: str,
    days_back: int = Query(60, ge=7, le=365, description="트렌드 분석 기간 (일)"),
    db: AsyncSession = Depends(get_db)
):
    """
    사용자의 관심사 트렌드 분석
    """
    try:
        # 사용자 존재 확인
        user = await get_user_by_id(db, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")
        
        # 트렌드 데이터 조회
        trends = await get_interest_trends(db, user_id, days_back)
        
        return InterestTrendResponse(
            user_id=user_id,
            analysis_period_days=days_back,
            trend_direction=trends.get('trend_direction', 'stable'),
            growing_interests=trends.get('growing_interests', []),
            declining_interests=trends.get('declining_interests', []),
            new_interests=trends.get('new_interests', []),
            consistent_interests=trends.get('consistent_interests', []),
            interest_diversity_score=trends.get('diversity_score', 0.5),
            engagement_trend=trends.get('engagement_trend', 'stable'),
            seasonal_patterns=trends.get('seasonal_patterns', {}),
            trend_insights=trends.get('insights', [])
        )
        
    except Exception as e:
        logger.error(f"관심사 트렌드 분석 중 오류 발생: {str(e)}")
        raise HTTPException(status_code=500, detail=f"관심사 트렌드 분석 중 오류가 발생했습니다: {str(e)}")

@router.get("/stats/{user_id}")
async def get_interest_statistics(
    user_id: str,
    days_back: int = Query(30, ge=1, le=365, description="통계 기간 (일)"),
    db: AsyncSession = Depends(get_db)
):
    """
    사용자의 관심사 통계 조회
    """
    try:
        # 사용자 존재 확인
        user = await get_user_by_id(db, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")
        
        # 사용자 관심사 조회
        interests = await get_user_interests(db, user_id)
        
        # 기본 통계 계산
        total_interests = len(interests)
        active_interests = len([i for i in interests if i.is_active])
        
        # 카테고리별 분포
        category_distribution = {}
        total_weight = 0
        for interest in interests:
            category = interest.category
            category_distribution[category] = category_distribution.get(category, 0) + 1
            total_weight += interest.weight
        
        # 평균 가중치
        average_weight = total_weight / total_interests if total_interests > 0 else 0
        
        # 최고 관심사 (가중치 기준)
        top_interest = max(interests, key=lambda x: x.weight) if interests else None
        
        return {
            "user_id": user_id,
            "stats_period": {
                "start_date": datetime.now() - timedelta(days=days_back),
                "end_date": datetime.now()
            },
            "total_interests": total_interests,
            "active_interests": active_interests,
            "interests_by_category": category_distribution,
            "average_weight": round(average_weight, 2),
            "top_interest": {
                "keyword": top_interest.keyword,
                "category": top_interest.category,
                "weight": top_interest.weight
            } if top_interest else None,
            "most_mentioned_interests": [i.keyword for i in sorted(interests, key=lambda x: x.mentioned_count, reverse=True)[:3]],
            "engagement_score": round(average_weight * 10, 1),
            "diversity_score": len(category_distribution),
            "activity_pattern": {
                "most_active_category": max(category_distribution.items(), key=lambda x: x[1])[0] if category_distribution else None,
                "least_active_category": min(category_distribution.items(), key=lambda x: x[1])[0] if category_distribution else None
            }
        }
        
    except Exception as e:
        logger.error(f"관심사 통계 조회 중 오류 발생: {str(e)}")
        raise HTTPException(status_code=500, detail=f"관심사 통계 조회 중 오류가 발생했습니다: {str(e)}")

# 관심사 기반 컨텐츠 추천

@router.get("/content/{user_id}")
async def get_interest_based_content(
    user_id: str,
    content_type: str = Query("all", description="컨텐츠 유형 (all, conversation, activity, learning)"),
    limit: int = Query(10, ge=1, le=50, description="추천 개수"),
    db: AsyncSession = Depends(get_db)
):
    """
    관심사 기반 컨텐츠 추천
    """
    try:
        # 사용자 존재 확인
        user = await get_user_by_id(db, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")
        
        # 사용자 관심사 조회
        interests = await get_user_interests(db, user_id)
        
        # 관심사별 컨텐츠 생성
        content_recommendations = []
        
        for interest in interests:
            category = interest.category
            interest_level = interest.interest_level
            keywords = interest.keywords
            
            # 카테고리별 컨텐츠 추천 로직
            if category == "정원가꾸기":
                if content_type in ["all", "conversation"]:
                    content_recommendations.append({
                        "type": "conversation_topic",
                        "title": "계절별 정원 관리 이야기",
                        "description": "지금 계절에 맞는 정원 관리 방법에 대해 이야기해보세요",
                        "category": category,
                        "interest_level": interest_level
                    })
                if content_type in ["all", "activity"]:
                    content_recommendations.append({
                        "type": "activity",
                        "title": "실내 허브 기르기",
                        "description": "작은 화분으로 시작하는 허브 재배 활동",
                        "category": category,
                        "interest_level": interest_level
                    })
            
            elif category == "요리":
                if content_type in ["all", "conversation"]:
                    content_recommendations.append({
                        "type": "conversation_topic",
                        "title": "추억의 요리 레시피",
                        "description": "어릴 때 먹었던 추억의 음식 이야기를 나눠보세요",
                        "category": category,
                        "interest_level": interest_level
                    })
                if content_type in ["all", "learning"]:
                    content_recommendations.append({
                        "type": "learning",
                        "title": "간단한 건강 요리법",
                        "description": "영양가 있고 만들기 쉬운 요리 방법 배우기",
                        "category": category,
                        "interest_level": interest_level
                    })
            
            elif category == "독서":
                if content_type in ["all", "conversation"]:
                    content_recommendations.append({
                        "type": "conversation_topic",
                        "title": "인생 책 추천",
                        "description": "감동받았던 책이나 추천하고 싶은 책에 대해 이야기해보세요",
                        "category": category,
                        "interest_level": interest_level
                    })
            
            # 더 많은 카테고리 추가 가능...
        
        # 관심도 순으로 정렬하고 제한
        content_recommendations.sort(key=lambda x: x['interest_level'], reverse=True)
        content_recommendations = content_recommendations[:limit]
        
        return {
            "user_id": user_id,
            "content_type": content_type,
            "recommendations": content_recommendations,
            "total_count": len(content_recommendations),
            "based_on_interests": len(interests),
            "generated_at": datetime.now()
        }
        
    except Exception as e:
        logger.error(f"관심사 기반 컨텐츠 추천 중 오류 발생: {str(e)}")
        raise HTTPException(status_code=500, detail=f"관심사 기반 컨텐츠 추천 중 오류가 발생했습니다: {str(e)}")

@router.get("/topics/{user_id}")
async def get_conversation_topics(
    user_id: str,
    mood: Optional[str] = Query(None, description="현재 기분 (happy, sad, neutral 등)"),
    time_of_day: Optional[str] = Query(None, description="시간대 (morning, afternoon, evening)"),
    limit: int = Query(5, ge=1, le=20, description="추천 개수"),
    db: AsyncSession = Depends(get_db)
):
    """
    관심사 기반 대화 주제 추천
    """
    try:
        # 사용자 존재 확인
        user = await get_user_by_id(db, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")
        
        # 사용자 관심사 조회
        interests = await get_user_interests(db, user_id)
        
        # 최근 감정 상태 조회
        if not mood:
            recent_emotions = await get_user_recent_emotions(db, user_id, days_back=1, limit=1)
            if recent_emotions:
                mood = recent_emotions[0].emotion
        
        # 시간대 기본값 설정
        if not time_of_day:
            current_hour = datetime.now().hour
            if 6 <= current_hour < 12:
                time_of_day = "morning"
            elif 12 <= current_hour < 18:
                time_of_day = "afternoon"
            else:
                time_of_day = "evening"
        
        # 관심사별 대화 주제 생성
        conversation_topics = []
        
        for interest in interests[:limit]:
            category = interest.category
            interest_level = interest.interest_level
            
            # 기분과 시간대에 따른 주제 조정
            if mood == "happy":
                if category == "정원가꾸기":
                    conversation_topics.append({
                        "topic": "오늘 정원에서 발견한 새로운 변화",
                        "starter": "정원에서 새로 피어난 꽃이나 자란 식물이 있나요?",
                        "category": category,
                        "mood_match": "happy",
                        "time_relevance": time_of_day
                    })
                elif category == "요리":
                    conversation_topics.append({
                        "topic": "기분 좋은 날의 특별한 요리",
                        "starter": "기분이 좋을 때 만들어보고 싶은 요리가 있나요?",
                        "category": category,
                        "mood_match": "happy",
                        "time_relevance": time_of_day
                    })
            elif mood == "lonely":
                if category == "가족":
                    conversation_topics.append({
                        "topic": "가족과의 소중한 추억",
                        "starter": "가족과 함께했던 특별한 순간들을 떠올려보세요",
                        "category": category,
                        "mood_match": "lonely",
                        "time_relevance": time_of_day
                    })
            
            # 기본 주제 (기분에 관계없이)
            if len(conversation_topics) < limit:
                conversation_topics.append({
                    "topic": f"{category} 관련 일상 이야기",
                    "starter": f"{category}에 대한 요즘 관심사나 경험을 들려주세요",
                    "category": category,
                    "mood_match": "neutral",
                    "time_relevance": time_of_day
                })
        
        return {
            "user_id": user_id,
            "current_mood": mood,
            "time_of_day": time_of_day,
            "conversation_topics": conversation_topics[:limit],
            "total_topics": len(conversation_topics[:limit]),
            "based_on_interests": len(interests),
            "generated_at": datetime.now()
        }
        
    except Exception as e:
        logger.error(f"대화 주제 추천 중 오류 발생: {str(e)}")
        raise HTTPException(status_code=500, detail=f"대화 주제 추천 중 오류가 발생했습니다: {str(e)}")

@router.post("/bulk-update/{user_id}")
async def bulk_update_interests(
    user_id: str,
    interests_data: List[InterestCreate],
    db: AsyncSession = Depends(get_db)
):
    """
    관심사 일괄 업데이트
    """
    try:
        # 사용자 존재 확인
        user = await get_user_by_id(db, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")
        
        # 기존 관심사 조회
        existing_interests = await get_user_interests(db, user_id)
        existing_categories = {interest.category for interest in existing_interests}
        
        created_interests = []
        updated_interests = []
        
        for interest_data in interests_data:
            if interest_data.category in existing_categories:
                # 기존 관심사 업데이트
                existing_interest = next(
                    (interest for interest in existing_interests if interest.category == interest_data.category),
                    None
                )
                if existing_interest:
                    update_data = InterestUpdate(
                        interest_level=interest_data.interest_level,
                        keywords=interest_data.keywords,
                        notes=interest_data.notes
                    )
                    updated_interest = await update_interest(db, existing_interest.id, update_data)
                    if updated_interest:
                        updated_interests.append(updated_interest)
            else:
                # 새 관심사 생성
                new_interest = await create_interest(db, interest_data)
                if new_interest:
                    created_interests.append(new_interest)
        
        logger.info(f"관심사 일괄 업데이트 완료 - 사용자: {user_id}, 생성: {len(created_interests)}, 업데이트: {len(updated_interests)}")
        
        return {
            "message": "관심사 일괄 업데이트가 완료되었습니다",
            "user_id": user_id,
            "created_count": len(created_interests),
            "updated_count": len(updated_interests),
            "total_processed": len(interests_data),
            "created_interests": [interest.id for interest in created_interests],
            "updated_interests": [interest.id for interest in updated_interests]
        }
        
    except Exception as e:
        logger.error(f"관심사 일괄 업데이트 중 오류 발생: {str(e)}")
        raise HTTPException(status_code=500, detail=f"관심사 일괄 업데이트 중 오류가 발생했습니다: {str(e)}") 