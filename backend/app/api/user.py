"""
사용자 API 라우터

사용자 등록, 조회, 수정, 삭제 등의 기능을 제공합니다.
"""

from typing import List, Optional
import logging
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.user import (
    UserCreate, UserResponse, UserUpdate, UserProfileUpdate,
    UserSearchResponse, UserStatsResponse, UserListResponse
)
from app.crud.user import (
    create_user, get_user_by_id, update_user,
    delete_user, search_users, get_users, get_users_list, get_user_by_name, get_all_users
)
from app.crud.chat_log import get_user_chat_history
from app.crud.emotion import get_user_recent_emotions
from app.services import analyze_user_profile, get_personalized_recommendations

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/users", tags=["users"])

@router.post("/register", response_model=UserResponse)
async def register_user(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    새로운 사용자 등록
    """
    try:
        # 중복 이름 확인 (선택사항)
        existing_user = await get_user_by_name(db, user_data.name)
        if existing_user:
            # 중복되면 숫자 추가
            user_data.name = f"{user_data.name}_{len(await get_all_users(db)) + 1}"
        
        # 사용자 생성
        new_user = await create_user(db, user_data)
        
        logger.info(f"새 사용자 등록 완료: {new_user.name} (ID: {new_user.id})")
        
        return UserResponse(
            id=new_user.id,
            name=new_user.name,
            age=new_user.age,
            gender=new_user.gender,
            speech_style=new_user.speech_style,
            phone=new_user.phone,
            profile_image=new_user.profile_image,
            is_active=new_user.is_active,
            last_login=new_user.last_login,
            created_at=new_user.created_at,
            updated_at=new_user.updated_at,
            display_name=new_user.display_name,
            age_group=new_user.age_group
        )
        
    except Exception as e:
        logger.error(f"사용자 등록 중 오류 발생: {str(e)}")
        raise HTTPException(status_code=500, detail=f"사용자 등록 중 오류가 발생했습니다: {str(e)}")

@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    사용자 정보 조회
    """
    try:
        user = await get_user_by_id(db, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")
        
        return UserResponse(
            id=user.id,
            name=user.name,
            age=user.age,
            gender=user.gender,
            speech_style=user.speech_style,
            phone=user.phone,
            profile_image=user.profile_image,
            is_active=user.is_active,
            last_login=user.last_login,
            created_at=user.created_at,
            updated_at=user.updated_at
        )
        
    except Exception as e:
        logger.error(f"사용자 조회 중 오류 발생: {str(e)}")
        raise HTTPException(status_code=500, detail=f"사용자 조회 중 오류가 발생했습니다: {str(e)}")

@router.put("/{user_id}", response_model=UserResponse)
async def update_user_info(
    user_id: str,
    user_data: UserUpdate,
    db: AsyncSession = Depends(get_db)
):
    """
    사용자 정보 수정
    """
    try:
        # 사용자 존재 확인
        existing_user = await get_user_by_id(db, user_id)
        if not existing_user:
            raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")
        
        # 사용자 정보 업데이트
        updated_user = await update_user(db, user_id, user_data)
        if not updated_user:
            raise HTTPException(status_code=500, detail="사용자 정보 업데이트에 실패했습니다")
        
        logger.info(f"사용자 정보 업데이트 완료 - ID: {user_id}")
        
        return UserResponse(
            id=updated_user.id,
            name=updated_user.name,
            age=updated_user.age,
            gender=updated_user.gender,
            speech_style=updated_user.speech_style,
            phone=updated_user.phone,
            profile_image=updated_user.profile_image,
            is_active=updated_user.is_active,
            last_login=updated_user.last_login,
            created_at=updated_user.created_at,
            updated_at=updated_user.updated_at
        )
        
    except Exception as e:
        logger.error(f"사용자 정보 수정 중 오류 발생: {str(e)}")
        raise HTTPException(status_code=500, detail=f"사용자 정보 수정 중 오류가 발생했습니다: {str(e)}")

@router.delete("/{user_id}")
async def delete_user_account(
    user_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    사용자 계정 삭제
    """
    try:
        # 사용자 존재 확인
        user = await get_user_by_id(db, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")
        
        # 사용자 삭제
        success = await delete_user(db, user_id)
        if not success:
            raise HTTPException(status_code=500, detail="사용자 삭제에 실패했습니다")
        
        logger.info(f"사용자 계정 삭제 완료 - ID: {user_id}")
        
        return {"message": "사용자 계정이 성공적으로 삭제되었습니다", "user_id": user_id}
        
    except Exception as e:
        logger.error(f"사용자 삭제 중 오류 발생: {str(e)}")
        raise HTTPException(status_code=500, detail=f"사용자 삭제 중 오류가 발생했습니다: {str(e)}")

@router.get("/", response_model=UserListResponse)
async def get_users_list_endpoint(
    skip: int = Query(0, ge=0, description="건너뛸 사용자 수"),
    limit: int = Query(100, ge=1, le=1000, description="조회할 최대 사용자 수"),
    search: Optional[str] = Query(None, description="검색어 (이름 또는 이메일)"),
    is_active: Optional[bool] = Query(None, description="활성 상태 필터"),
    db: AsyncSession = Depends(get_db)
):
    """
    사용자 목록 조회
    """
    try:
        if search:
            # 검색 기능
            users = await search_users(db, search, limit, skip)
            total_count = len(users)  # 검색 결과의 정확한 카운트는 별도 쿼리 필요
        else:
            # 전체 목록 조회
            users, total_count = await get_users_list(db, skip, limit, is_active)
        
        user_responses = []
        for user in users:
            user_responses.append(UserResponse(
                id=user.id,
                name=user.name,
                age=user.age,
                gender=user.gender,
                speech_style=user.speech_style,
                phone=user.phone,
                profile_image=user.profile_image,
                is_active=user.is_active,
                last_login=user.last_login,
                created_at=user.created_at,
                updated_at=user.updated_at
            ))
        
        return UserListResponse(
            users=user_responses,
            total_count=total_count,
            skip=skip,
            limit=limit,
            has_more=(skip + limit < total_count)
        )
        
    except Exception as e:
        logger.error(f"사용자 목록 조회 중 오류 발생: {str(e)}")
        raise HTTPException(status_code=500, detail=f"사용자 목록 조회 중 오류가 발생했습니다: {str(e)}")

@router.get("/{user_id}/stats", response_model=UserStatsResponse)
async def get_user_statistics(
    user_id: str,
    days_back: int = Query(30, ge=1, le=365, description="통계 기간 (일)"),
    db: AsyncSession = Depends(get_db)
):
    """
    사용자 활동 통계 조회
    """
    try:
        # 사용자 존재 확인
        user = await get_user_by_id(db, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")
        
        # 통계 데이터 조회
        stats = await get_user_stats(db, user_id, days_back)
        
        return UserStatsResponse(
            user_id=user_id,
            period_days=days_back,
            total_chat_messages=stats.get('total_chat_messages', 0),
            total_chat_sessions=stats.get('total_chat_sessions', 0),
            avg_session_duration=stats.get('avg_session_duration', 0),
            most_frequent_emotion=stats.get('most_frequent_emotion', 'neutral'),
            emotion_distribution=stats.get('emotion_distribution', {}),
            daily_activity=stats.get('daily_activity', {}),
            last_activity=stats.get('last_activity'),
            total_active_days=stats.get('total_active_days', 0)
        )
        
    except Exception as e:
        logger.error(f"사용자 통계 조회 중 오류 발생: {str(e)}")
        raise HTTPException(status_code=500, detail=f"사용자 통계 조회 중 오류가 발생했습니다: {str(e)}")

@router.get("/{user_id}/profile/analysis")
async def get_user_profile_analysis(
    user_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    사용자 프로필 분석 결과 조회
    """
    try:
        # 사용자 존재 확인
        user = await get_user_by_id(db, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")
        
        # 최근 채팅 기록 조회
        recent_chats = await get_user_chat_history(db, user_id, limit=100)
        chat_history = []
        for chat in recent_chats:
            chat_history.append({
                'message': chat.message,
                'role': chat.role,
                'timestamp': chat.timestamp
            })
        
        # 감정 기록 조회
        recent_emotions = await get_user_recent_emotions(db, user_id, days_back=30)
        emotion_history = []
        for emotion in recent_emotions:
            emotion_history.append({
                'emotion': emotion.emotion,
                'intensity': emotion.intensity,
                'timestamp': emotion.timestamp
            })
        
        # 프로필 분석 실행
        profile_analysis = await analyze_user_profile(
            user_id=user_id,
            chat_history=chat_history,
            emotion_history=emotion_history
        )
        
        return {
            "user_id": user_id,
            "analysis_timestamp": datetime.now(),
            "interests": profile_analysis.get('interests', {}),
            "communication_style": profile_analysis.get('communication_style', {}),
            "personality_traits": profile_analysis.get('personality_traits', {}),
            "data_sufficiency": {
                "chat_messages": len(chat_history),
                "emotion_records": len(emotion_history),
                "analysis_confidence": "high" if len(chat_history) > 50 else "medium" if len(chat_history) > 20 else "low"
            }
        }
        
    except Exception as e:
        logger.error(f"사용자 프로필 분석 중 오류 발생: {str(e)}")
        raise HTTPException(status_code=500, detail=f"사용자 프로필 분석 중 오류가 발생했습니다: {str(e)}")

@router.get("/{user_id}/recommendations")
async def get_user_recommendations(
    user_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    사용자 맞춤 추천 조회
    """
    try:
        # 사용자 존재 확인
        user = await get_user_by_id(db, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")
        
        # 프로필 분석 데이터 조회
        recent_chats = await get_user_chat_history(db, user_id, limit=50)
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
        
        return {
            "user_id": user_id,
            "recommendation_timestamp": datetime.now(),
            "recommendations": recommendations.get('recommendations', {}),
            "personalization_score": recommendations.get('personalization_score', 0.0),
            "based_on": {
                "chat_messages": len(chat_history),
                "emotion_records": len(emotion_history),
                "interests_identified": len(profile_analysis.get('interests', {}).get('interests', {})),
                "personality_traits_identified": len(profile_analysis.get('personality_traits', {}).get('traits', {}))
            }
        }
        
    except Exception as e:
        logger.error(f"사용자 추천 조회 중 오류 발생: {str(e)}")
        raise HTTPException(status_code=500, detail=f"사용자 추천 조회 중 오류가 발생했습니다: {str(e)}")

@router.put("/{user_id}/profile", response_model=UserResponse)
async def update_user_profile_endpoint(
    user_id: str,
    profile_data: UserProfileUpdate,
    db: AsyncSession = Depends(get_db)
):
    """
    사용자 프로필 업데이트
    """
    try:
        # 사용자 존재 확인
        user = await get_user_by_id(db, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")
        
        # 프로필 업데이트
        updated_user = await update_user_profile(db, user_id, profile_data)
        if not updated_user:
            raise HTTPException(status_code=500, detail="프로필 업데이트에 실패했습니다")
        
        logger.info(f"사용자 프로필 업데이트 완료 - ID: {user_id}")
        
        return UserResponse(
            id=updated_user.id,
            name=updated_user.name,
            age=updated_user.age,
            gender=updated_user.gender,
            speech_style=updated_user.speech_style,
            phone=updated_user.phone,
            profile_image=updated_user.profile_image,
            is_active=updated_user.is_active,
            last_login=updated_user.last_login,
            created_at=updated_user.created_at,
            updated_at=updated_user.updated_at
        )
        
    except Exception as e:
        logger.error(f"사용자 프로필 업데이트 중 오류 발생: {str(e)}")
        raise HTTPException(status_code=500, detail=f"사용자 프로필 업데이트 중 오류가 발생했습니다: {str(e)}")

@router.get("/{user_id}/activity")
async def get_user_activity(
    user_id: str,
    days_back: int = Query(7, ge=1, le=90, description="활동 조회 기간 (일)"),
    db: AsyncSession = Depends(get_db)
):
    """
    사용자 활동 요약 조회
    """
    try:
        # 사용자 존재 확인
        user = await get_user_by_id(db, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")
        
        # 활동 요약 조회
        activity_summary = await get_user_activity_summary(db, user_id, days_back)
        
        return {
            "user_id": user_id,
            "period_days": days_back,
            "activity_summary": activity_summary,
            "generated_at": datetime.now()
        }
        
    except Exception as e:
        logger.error(f"사용자 활동 조회 중 오류 발생: {str(e)}")
        raise HTTPException(status_code=500, detail=f"사용자 활동 조회 중 오류가 발생했습니다: {str(e)}")

@router.post("/{user_id}/login")
async def user_login(
    user_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    사용자 로그인 (last_login 업데이트)
    """
    try:
        # 사용자 존재 확인
        user = await get_user_by_id(db, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")
        
        # 마지막 로그인 시간 업데이트
        update_data = UserUpdate(last_login=datetime.now())
        updated_user = await update_user(db, user_id, update_data)
        
        logger.info(f"사용자 로그인 - ID: {user_id}")
        
        return {
            "message": "로그인 성공",
            "user_id": user_id,
            "login_time": datetime.now(),
            "user_name": updated_user.name
        }
        
    except Exception as e:
        logger.error(f"사용자 로그인 중 오류 발생: {str(e)}")
        raise HTTPException(status_code=500, detail=f"로그인 처리 중 오류가 발생했습니다: {str(e)}") 