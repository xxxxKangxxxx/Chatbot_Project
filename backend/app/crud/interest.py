"""
관심사 관련 CRUD 연산
=====================================================

관심사 생성, 조회, 수정, 삭제 등의 데이터베이스 연산을 처리합니다.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy import and_, or_, func, desc, asc
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import uuid

from app.models.interest import Interest, InterestLog
from app.schemas.interest import (
    InterestCreate, InterestUpdate, InterestLogCreate
)


async def create_interest(db: AsyncSession, interest: InterestCreate) -> Interest:
    """새 관심사 생성"""
    interest_data = interest.dict(exclude={'context'})  # context 필드 제외
    interest_data['id'] = str(uuid.uuid4())  # UUID 생성
    new_interest = Interest(**interest_data)
    
    db.add(new_interest)
    await db.commit()
    await db.refresh(new_interest)
    return new_interest


async def get_interest(db: AsyncSession, interest_id: str) -> Optional[Interest]:
    """관심사 ID로 조회"""
    result = await db.execute(
        select(Interest).where(Interest.id == interest_id)
    )
    return result.scalar_one_or_none()


async def get_user_interests(
    db: AsyncSession,
    user_id: str,
    limit: int = 50,
    offset: int = 0
) -> List[Interest]:
    """사용자의 관심사 목록 조회"""
    query = select(Interest).where(Interest.user_id == user_id)
    query = query.order_by(desc(Interest.created_at))
    query = query.offset(offset).limit(limit)
    
    result = await db.execute(query)
    return result.scalars().all()


async def update_interest(
    db: AsyncSession,
    interest_id: str,
    interest_update: InterestUpdate
) -> Optional[Interest]:
    """관심사 정보 업데이트"""
    result = await db.execute(
        select(Interest).where(Interest.id == interest_id)
    )
    interest = result.scalar_one_or_none()
    
    if not interest:
        return None
    
    # 업데이트할 데이터만 추출
    update_data = interest_update.dict(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(interest, field, value)
    
    interest.updated_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(interest)
    return interest


async def delete_interest(db: AsyncSession, interest_id: str) -> bool:
    """관심사 삭제"""
    result = await db.execute(
        select(Interest).where(Interest.id == interest_id)
    )
    interest = result.scalar_one_or_none()
    
    if not interest:
        return False
    
    await db.delete(interest)
    await db.commit()
    return True


async def create_interest_log(db: AsyncSession, log_data: InterestLogCreate) -> InterestLog:
    """관심사 로그 생성"""
    log_dict = log_data.dict()
    log_dict['id'] = str(uuid.uuid4())  # UUID 생성
    new_log = InterestLog(**log_dict)
    
    db.add(new_log)
    await db.commit()
    await db.refresh(new_log)
    return new_log


async def get_user_interest_logs(
    db: AsyncSession,
    user_id: str,
    days_back: int = 30,
    limit: int = 100
) -> List[InterestLog]:
    """사용자의 관심사 로그 조회"""
    cutoff_date = datetime.utcnow() - timedelta(days=days_back)
    
    query = select(InterestLog).where(
        and_(
            InterestLog.user_id == user_id,
            InterestLog.created_at >= cutoff_date
        )
    ).order_by(desc(InterestLog.created_at)).limit(limit)
    
    result = await db.execute(query)
    return result.scalars().all()


async def analyze_user_interests(
    db: AsyncSession,
    user_id: str,
    days_back: int = 30
) -> Dict[str, Any]:
    """사용자 관심사 분석"""
    cutoff_date = datetime.utcnow() - timedelta(days=days_back)
    
    # 관심사별 언급 횟수
    interest_counts_result = await db.execute(
        select(InterestLog.category, func.count(InterestLog.id))
        .where(
            and_(
                InterestLog.user_id == user_id,
                InterestLog.created_at >= cutoff_date
            )
        )
        .group_by(InterestLog.category)
        .order_by(desc(func.count(InterestLog.id)))
    )
    
    interest_distribution = {}
    for category, count in interest_counts_result.fetchall():
        interest_distribution[category.value] = count
    
    # 총 관심사 기록 수
    total_logs_result = await db.execute(
        select(func.count(InterestLog.id))
        .where(
            and_(
                InterestLog.user_id == user_id,
                InterestLog.created_at >= cutoff_date
            )
        )
    )
    total_logs = total_logs_result.scalar() or 0
    
    # 주요 관심사 (상위 3개)
    top_interests = list(interest_distribution.keys())[:3]
    
    return {
        "total_logs": total_logs,
        "interest_distribution": interest_distribution,
        "top_interests": top_interests,
        "analysis_period_days": days_back
    } 