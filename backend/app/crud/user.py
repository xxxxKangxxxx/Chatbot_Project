"""
사용자 관련 CRUD 연산
=====================================================

사용자 생성, 조회, 수정, 삭제 등의 데이터베이스 연산을 처리합니다.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy import and_, or_, func, desc, asc
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta

from app.models.user import User
from app.schemas.user import (
    UserCreate, UserUpdate, UserSearchRequest, GenderEnum
)


async def create_user(db: AsyncSession, user: UserCreate) -> User:
    """새 사용자 생성"""
    import uuid
    
    user_data = user.dict()
    user_data['id'] = str(uuid.uuid4())  # UUID 생성
    new_user = User(**user_data)
    
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user


async def get_user(db: AsyncSession, user_id: str) -> Optional[User]:
    """사용자 ID로 조회"""
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    return result.scalar_one_or_none()


async def get_user_by_id(db: AsyncSession, user_id: str) -> Optional[User]:
    """사용자 ID로 조회 (별칭)"""
    return await get_user(db, user_id)


async def get_user_by_phone(db: AsyncSession, phone: str) -> Optional[User]:
    """전화번호로 사용자 조회"""
    result = await db.execute(
        select(User).where(User.phone == phone)
    )
    return result.scalar_one_or_none()


async def get_users(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 100,
    is_active: Optional[bool] = None
) -> List[User]:
    """사용자 목록 조회"""
    query = select(User)
    
    if is_active is not None:
        query = query.where(User.is_active == is_active)
    
    query = query.offset(skip).limit(limit).order_by(desc(User.created_at))
    
    result = await db.execute(query)
    return result.scalars().all()


async def get_users_list(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 100,
    is_active: Optional[bool] = None
) -> tuple[List[User], int]:
    """사용자 목록과 전체 개수 조회"""
    # 전체 개수 조회
    count_query = select(func.count(User.id))
    if is_active is not None:
        count_query = count_query.where(User.is_active == is_active)
    
    total_result = await db.execute(count_query)
    total_count = total_result.scalar() or 0
    
    # 사용자 목록 조회
    users = await get_users(db, skip, limit, is_active)
    
    return users, total_count


async def update_user(
    db: AsyncSession,
    user_id: str,
    user_update: UserUpdate
) -> Optional[User]:
    """사용자 정보 업데이트"""
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        return None
    
    # 업데이트할 데이터만 추출
    update_data = user_update.dict(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(user, field, value)
    
    user.updated_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(user)
    return user


async def delete_user(db: AsyncSession, user_id: str) -> bool:
    """사용자 삭제 (소프트 삭제)"""
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        return False
    
    user.is_active = False
    user.updated_at = datetime.utcnow()
    
    await db.commit()
    return True


async def search_users(
    db: AsyncSession,
    search_request: UserSearchRequest
) -> tuple[List[User], int]:
    """사용자 검색"""
    query = select(User)
    count_query = select(func.count(User.id))
    
    # 검색 조건 적용
    conditions = []
    
    if search_request.query:
        search_term = f"%{search_request.query}%"
        conditions.append(
            or_(
                User.name.ilike(search_term),
                User.phone.ilike(search_term)
            )
        )
    
    if search_request.age_min is not None:
        conditions.append(User.age >= search_request.age_min)
    
    if search_request.age_max is not None:
        conditions.append(User.age <= search_request.age_max)
    
    if search_request.gender is not None:
        conditions.append(User.gender == search_request.gender)
    
    if search_request.is_active is not None:
        conditions.append(User.is_active == search_request.is_active)
    
    # 조건 적용
    if conditions:
        query = query.where(and_(*conditions))
        count_query = count_query.where(and_(*conditions))
    
    # 전체 개수 조회
    total_result = await db.execute(count_query)
    total_count = total_result.scalar()
    
    # 페이지네이션 및 정렬
    query = query.offset(search_request.offset).limit(search_request.limit)
    query = query.order_by(desc(User.created_at))
    
    result = await db.execute(query)
    users = result.scalars().all()
    
    return users, total_count


async def get_user_with_stats(db: AsyncSession, user_id: int) -> Optional[Dict[str, Any]]:
    """사용자 정보와 통계 함께 조회"""
    # 사용자 기본 정보
    user_result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = user_result.scalar_one_or_none()
    
    if not user:
        return None
    
    # 관련 통계 조회 (다른 테이블과 조인)
    from app.models.chat_log import ChatLog, ChatSession
    from app.models.emotion import Emotion
    from app.models.medication import MedicationSchedule
    from app.models.interest import Interest
    
    # 채팅 통계
    chat_count_result = await db.execute(
        select(func.count(ChatLog.id)).where(ChatLog.user_id == user_id)
    )
    total_messages = chat_count_result.scalar() or 0
    
    session_count_result = await db.execute(
        select(func.count(ChatSession.id)).where(ChatSession.user_id == user_id)
    )
    total_sessions = session_count_result.scalar() or 0
    
    # 감정 통계
    emotion_count_result = await db.execute(
        select(func.count(Emotion.id)).where(Emotion.user_id == user_id)
    )
    emotion_count = emotion_count_result.scalar() or 0
    
    # 최근 감정 조회
    recent_emotion_result = await db.execute(
        select(Emotion.emotion_type)
        .where(Emotion.user_id == user_id)
        .order_by(desc(Emotion.created_at))
        .limit(1)
    )
    recent_emotion = recent_emotion_result.scalar()
    
    # 약물 통계
    medication_count_result = await db.execute(
        select(func.count(MedicationSchedule.id))
        .where(
            and_(
                MedicationSchedule.user_id == user_id,
                MedicationSchedule.is_active == True
            )
        )
    )
    medication_count = medication_count_result.scalar() or 0
    
    # 관심사 통계
    interest_count_result = await db.execute(
        select(func.count(Interest.id))
        .where(
            and_(
                Interest.user_id == user_id,
                Interest.is_active == True
            )
        )
    )
    interest_count = interest_count_result.scalar() or 0
    
    return {
        "user": user,
        "stats": {
            "total_messages": total_messages,
            "total_sessions": total_sessions,
            "emotion_count": emotion_count,
            "recent_emotion": recent_emotion,
            "medication_count": medication_count,
            "interest_count": interest_count
        }
    }


async def update_user_last_login(db: AsyncSession, user_id: int) -> bool:
    """사용자 마지막 로그인 시간 업데이트"""
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        return False
    
    user.last_login = datetime.utcnow()
    user.updated_at = datetime.utcnow()
    
    await db.commit()
    return True


async def get_active_users_count(db: AsyncSession) -> int:
    """활성 사용자 수 조회"""
    result = await db.execute(
        select(func.count(User.id)).where(User.is_active == True)
    )
    return result.scalar() or 0


async def get_users_by_age_group(
    db: AsyncSession,
    min_age: int,
    max_age: int
) -> List[User]:
    """연령대별 사용자 조회"""
    result = await db.execute(
        select(User).where(
            and_(
                User.age >= min_age,
                User.age <= max_age,
                User.is_active == True
            )
        )
    )
    return result.scalars().all()


async def get_users_by_gender(
    db: AsyncSession,
    gender: GenderEnum
) -> List[User]:
    """성별로 사용자 조회"""
    result = await db.execute(
        select(User).where(
            and_(
                User.gender == gender,
                User.is_active == True
            )
        )
    )
    return result.scalars().all()


async def get_recent_users(
    db: AsyncSession,
    days: int = 7,
    limit: int = 50
) -> List[User]:
    """최근 가입한 사용자 조회"""
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    result = await db.execute(
        select(User)
        .where(User.created_at >= cutoff_date)
        .order_by(desc(User.created_at))
        .limit(limit)
    )
    return result.scalars().all()


async def get_inactive_users(
    db: AsyncSession,
    days: int = 30,
    limit: int = 100
) -> List[User]:
    """비활성 사용자 조회 (마지막 로그인 기준)"""
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    result = await db.execute(
        select(User)
        .where(
            and_(
                User.is_active == True,
                or_(
                    User.last_login < cutoff_date,
                    User.last_login.is_(None)
                )
            )
        )
        .order_by(asc(User.last_login))
        .limit(limit)
    )
    return result.scalars().all()


async def bulk_update_users(
    db: AsyncSession,
    user_ids: List[int],
    update_data: Dict[str, Any]
) -> int:
    """사용자 일괄 업데이트"""
    if not user_ids:
        return 0
    
    # 업데이트할 사용자들 조회
    result = await db.execute(
        select(User).where(User.id.in_(user_ids))
    )
    users = result.scalars().all()
    
    updated_count = 0
    for user in users:
        for field, value in update_data.items():
            if hasattr(user, field):
                setattr(user, field, value)
        user.updated_at = datetime.utcnow()
        updated_count += 1
    
    await db.commit()
    return updated_count


async def get_user_statistics(db: AsyncSession) -> Dict[str, Any]:
    """전체 사용자 통계"""
    # 전체 사용자 수
    total_users_result = await db.execute(
        select(func.count(User.id))
    )
    total_users = total_users_result.scalar() or 0
    
    # 활성 사용자 수
    active_users_result = await db.execute(
        select(func.count(User.id)).where(User.is_active == True)
    )
    active_users = active_users_result.scalar() or 0
    
    # 성별 분포
    gender_stats_result = await db.execute(
        select(User.gender, func.count(User.id))
        .where(User.is_active == True)
        .group_by(User.gender)
    )
    gender_distribution = {
        gender: count for gender, count in gender_stats_result.fetchall()
    }
    
    # 연령대 분포
    age_stats_result = await db.execute(
        select(
            func.case(
                (User.age < 60, "중년"),
                (User.age < 70, "초고령"),
                else_="고령"
            ).label("age_group"),
            func.count(User.id)
        )
        .where(
            and_(
                User.is_active == True,
                User.age.is_not(None)
            )
        )
        .group_by("age_group")
    )
    age_distribution = {
        age_group: count for age_group, count in age_stats_result.fetchall()
    }
    
    # 최근 7일 가입자 수
    recent_cutoff = datetime.utcnow() - timedelta(days=7)
    recent_users_result = await db.execute(
        select(func.count(User.id))
        .where(User.created_at >= recent_cutoff)
    )
    recent_signups = recent_users_result.scalar() or 0
    
    # 평균 나이
    avg_age_result = await db.execute(
        select(func.avg(User.age))
        .where(
            and_(
                User.is_active == True,
                User.age.is_not(None)
            )
        )
    )
    avg_age = avg_age_result.scalar() or 0
    
    return {
        "total_users": total_users,
        "active_users": active_users,
        "inactive_users": total_users - active_users,
        "gender_distribution": gender_distribution,
        "age_distribution": age_distribution,
        "recent_signups": recent_signups,
        "avg_age": round(float(avg_age), 1) if avg_age else 0,
        "activation_rate": round(active_users / total_users * 100, 1) if total_users > 0 else 0
    }


async def check_user_exists(db: AsyncSession, user_id: int) -> bool:
    """사용자 존재 여부 확인"""
    result = await db.execute(
        select(func.count(User.id)).where(User.id == user_id)
    )
    return result.scalar() > 0


async def get_user_profile_summary(db: AsyncSession, user_id: int) -> Optional[Dict[str, Any]]:
    """사용자 프로필 요약 정보"""
    user = await get_user(db, user_id)
    if not user:
        return None
    
    # 기본 프로필 정보
    profile = {
        "id": user.id,
        "name": user.name,
        "age": user.age,
        "gender": user.gender,
        "speech_style": user.speech_style,
        "is_active": user.is_active,
        "created_at": user.created_at,
        "last_login": user.last_login,
        "display_name": f"{user.name}님" if user.name else "사용자님",
        "age_group": "미상" if not user.age else (
            "중년" if user.age < 60 else "초고령" if user.age < 70 else "고령"
        )
    }
    
    return profile 