"""
채팅 로그 관련 CRUD 연산
=====================================================

채팅 메시지, 세션 관리 등의 데이터베이스 연산을 처리합니다.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy import and_, or_, func, desc, asc
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timedelta
import uuid

from app.models.chat_log import ChatLog, ChatSession
from app.models.user import User
from app.schemas.chat import (
    ChatLogCreate, ChatSessionCreate, ChatHistoryRequest,
    RoleEnum, MessageTypeEnum
)


async def create_chat_log(db: AsyncSession, chat_log: ChatLogCreate) -> ChatLog:
    """새 채팅 로그 생성"""
    import uuid
    
    chat_data = chat_log.dict()
    chat_data['id'] = str(uuid.uuid4())  # UUID 생성
    new_chat_log = ChatLog(**chat_data)
    
    db.add(new_chat_log)
    await db.commit()
    await db.refresh(new_chat_log)
    return new_chat_log


async def create_chat_session(db: AsyncSession, session_data: ChatSessionCreate) -> ChatSession:
    """새 채팅 세션 생성"""
    import uuid
    
    session_dict = session_data.dict()
    session_dict['id'] = str(uuid.uuid4())  # UUID 생성
    new_session = ChatSession(**session_dict)
    
    db.add(new_session)
    await db.commit()
    await db.refresh(new_session)
    return new_session


async def get_chat_log(db: AsyncSession, log_id: int) -> Optional[ChatLog]:
    """채팅 로그 ID로 조회"""
    result = await db.execute(
        select(ChatLog).where(ChatLog.id == log_id)
    )
    return result.scalar_one_or_none()


async def get_chat_session(db: AsyncSession, session_id: str) -> Optional[ChatSession]:
    """채팅 세션 ID로 조회"""
    result = await db.execute(
        select(ChatSession).where(ChatSession.session_id == session_id)
    )
    return result.scalar_one_or_none()


async def get_or_create_session(
    db: AsyncSession,
    user_id: int,
    session_id: Optional[str] = None
) -> ChatSession:
    """세션 조회 또는 생성"""
    if session_id:
        session = await get_chat_session(db, session_id)
        if session:
            return session
    
    # 새 세션 생성
    new_session_id = session_id or str(uuid.uuid4())
    session_data = ChatSessionCreate(
        user_id=user_id,
        session_id=new_session_id
    )
    return await create_chat_session(db, session_data)


async def get_user_chat_logs(
    db: AsyncSession,
    user_id: int,
    session_id: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
) -> List[ChatLog]:
    """사용자의 채팅 로그 조회"""
    query = select(ChatLog).where(ChatLog.user_id == user_id)
    
    if session_id:
        query = query.where(ChatLog.session_id == session_id)
    
    query = query.order_by(desc(ChatLog.created_at)).offset(offset).limit(limit)
    
    result = await db.execute(query)
    return result.scalars().all()


async def get_chat_history(
    db: AsyncSession,
    request: ChatHistoryRequest
) -> Tuple[List[ChatLog], int]:
    """채팅 히스토리 조회"""
    query = select(ChatLog).where(ChatLog.user_id == request.user_id)
    count_query = select(func.count(ChatLog.id)).where(ChatLog.user_id == request.user_id)
    
    # 세션 필터
    if request.session_id:
        query = query.where(ChatLog.session_id == request.session_id)
        count_query = count_query.where(ChatLog.session_id == request.session_id)
    
    # 날짜 범위 필터
    if request.days:
        cutoff_date = datetime.utcnow() - timedelta(days=request.days)
        query = query.where(ChatLog.created_at >= cutoff_date)
        count_query = count_query.where(ChatLog.created_at >= cutoff_date)
    
    # 봇 메시지 포함 여부
    if not request.include_bot_messages:
        query = query.where(ChatLog.role == RoleEnum.USER)
        count_query = count_query.where(ChatLog.role == RoleEnum.USER)
    
    # 전체 개수 조회
    total_result = await db.execute(count_query)
    total_count = total_result.scalar()
    
    # 페이지네이션
    query = query.order_by(desc(ChatLog.created_at)).offset(request.offset).limit(request.limit)
    
    result = await db.execute(query)
    chat_logs = result.scalars().all()
    
    return chat_logs, total_count


async def get_recent_conversation(
    db: AsyncSession,
    user_id: int,
    session_id: Optional[str] = None,
    limit: int = 10
) -> List[ChatLog]:
    """최근 대화 내용 조회"""
    query = select(ChatLog).where(ChatLog.user_id == user_id)
    
    if session_id:
        query = query.where(ChatLog.session_id == session_id)
    
    query = query.order_by(desc(ChatLog.created_at)).limit(limit)
    
    result = await db.execute(query)
    logs = result.scalars().all()
    
    # 시간 순으로 정렬 (오래된 것부터)
    return list(reversed(logs))


async def update_chat_log(
    db: AsyncSession,
    log_id: int,
    update_data: Dict[str, Any]
) -> Optional[ChatLog]:
    """채팅 로그 업데이트"""
    result = await db.execute(
        select(ChatLog).where(ChatLog.id == log_id)
    )
    chat_log = result.scalar_one_or_none()
    
    if not chat_log:
        return None
    
    for field, value in update_data.items():
        if hasattr(chat_log, field):
            setattr(chat_log, field, value)
    
    await db.commit()
    await db.refresh(chat_log)
    return chat_log


async def update_session_stats(db: AsyncSession, session_id: str) -> bool:
    """세션 통계 업데이트"""
    session = await get_chat_session(db, session_id)
    if not session:
        return False
    
    # 세션의 메시지 수 계산
    message_count_result = await db.execute(
        select(func.count(ChatLog.id)).where(ChatLog.session_id == session_id)
    )
    message_count = message_count_result.scalar() or 0
    
    # 평균 감정 점수 계산
    avg_emotion_result = await db.execute(
        select(func.avg(ChatLog.emotion_score))
        .where(
            and_(
                ChatLog.session_id == session_id,
                ChatLog.emotion_score.is_not(None)
            )
        )
    )
    avg_emotion = avg_emotion_result.scalar()
    
    # 세션 정보 업데이트
    session.message_count = message_count
    session.avg_emotion_score = float(avg_emotion) if avg_emotion else None
    
    await db.commit()
    return True


async def end_chat_session(db: AsyncSession, session_id: str) -> bool:
    """채팅 세션 종료"""
    session = await get_chat_session(db, session_id)
    if not session:
        return False
    
    session.end_time = datetime.utcnow()
    await update_session_stats(db, session_id)
    
    await db.commit()
    return True


async def get_user_sessions(
    db: AsyncSession,
    user_id: int,
    limit: int = 20,
    offset: int = 0
) -> List[ChatSession]:
    """사용자의 채팅 세션 목록 조회"""
    result = await db.execute(
        select(ChatSession)
        .where(ChatSession.user_id == user_id)
        .order_by(desc(ChatSession.start_time))
        .offset(offset)
        .limit(limit)
    )
    return result.scalars().all()


async def get_active_sessions(
    db: AsyncSession,
    hours: int = 24,
    limit: int = 100
) -> List[ChatSession]:
    """활성 세션 조회"""
    cutoff_time = datetime.utcnow() - timedelta(hours=hours)
    
    result = await db.execute(
        select(ChatSession)
        .where(
            and_(
                ChatSession.start_time >= cutoff_time,
                ChatSession.end_time.is_(None)
            )
        )
        .order_by(desc(ChatSession.start_time))
        .limit(limit)
    )
    return result.scalars().all()


async def search_chat_logs(
    db: AsyncSession,
    user_id: int,
    search_query: str,
    limit: int = 50
) -> List[ChatLog]:
    """채팅 로그 검색"""
    search_term = f"%{search_query}%"
    
    result = await db.execute(
        select(ChatLog)
        .where(
            and_(
                ChatLog.user_id == user_id,
                ChatLog.message.ilike(search_term)
            )
        )
        .order_by(desc(ChatLog.created_at))
        .limit(limit)
    )
    return result.scalars().all()


async def get_chat_analytics(
    db: AsyncSession,
    user_id: int,
    days: int = 30
) -> Dict[str, Any]:
    """채팅 분석 데이터"""
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    # 총 메시지 수
    total_messages_result = await db.execute(
        select(func.count(ChatLog.id))
        .where(
            and_(
                ChatLog.user_id == user_id,
                ChatLog.created_at >= cutoff_date
            )
        )
    )
    total_messages = total_messages_result.scalar() or 0
    
    # 사용자/봇 메시지 수
    user_messages_result = await db.execute(
        select(func.count(ChatLog.id))
        .where(
            and_(
                ChatLog.user_id == user_id,
                ChatLog.role == RoleEnum.USER,
                ChatLog.created_at >= cutoff_date
            )
        )
    )
    user_messages = user_messages_result.scalar() or 0
    
    bot_messages = total_messages - user_messages
    
    # 세션 수
    session_count_result = await db.execute(
        select(func.count(ChatSession.id))
        .where(
            and_(
                ChatSession.user_id == user_id,
                ChatSession.start_time >= cutoff_date
            )
        )
    )
    session_count = session_count_result.scalar() or 0
    
    # 평균 감정 점수
    avg_emotion_result = await db.execute(
        select(func.avg(ChatLog.emotion_score))
        .where(
            and_(
                ChatLog.user_id == user_id,
                ChatLog.emotion_score.is_not(None),
                ChatLog.created_at >= cutoff_date
            )
        )
    )
    avg_emotion = avg_emotion_result.scalar()
    
    # 감정 분포
    emotion_distribution_result = await db.execute(
        select(ChatLog.emotion, func.count(ChatLog.id))
        .where(
            and_(
                ChatLog.user_id == user_id,
                ChatLog.emotion.is_not(None),
                ChatLog.created_at >= cutoff_date
            )
        )
        .group_by(ChatLog.emotion)
    )
    emotion_distribution = {
        emotion: count for emotion, count in emotion_distribution_result.fetchall()
    }
    
    # 시간대별 활동
    hourly_activity_result = await db.execute(
        select(
            func.extract('hour', ChatLog.created_at).label('hour'),
            func.count(ChatLog.id)
        )
        .where(
            and_(
                ChatLog.user_id == user_id,
                ChatLog.created_at >= cutoff_date
            )
        )
        .group_by('hour')
    )
    hourly_activity = {
        str(int(hour)): count for hour, count in hourly_activity_result.fetchall()
    }
    
    return {
        "total_messages": total_messages,
        "user_messages": user_messages,
        "bot_messages": bot_messages,
        "session_count": session_count,
        "avg_emotion_score": float(avg_emotion) if avg_emotion else None,
        "avg_messages_per_session": round(total_messages / session_count, 1) if session_count > 0 else 0,
        "emotion_distribution": emotion_distribution,
        "hourly_activity": hourly_activity
    }


async def get_conversation_context(
    db: AsyncSession,
    user_id: int,
    session_id: Optional[str] = None,
    limit: int = 5
) -> List[Dict[str, Any]]:
    """대화 컨텍스트 조회 (GPT 프롬프트용)"""
    query = select(ChatLog).where(ChatLog.user_id == user_id)
    
    if session_id:
        query = query.where(ChatLog.session_id == session_id)
    
    query = query.order_by(desc(ChatLog.created_at)).limit(limit)
    
    result = await db.execute(query)
    logs = result.scalars().all()
    
    # 시간 순으로 정렬하고 컨텍스트 형태로 변환
    context = []
    for log in reversed(logs):
        context.append({
            "role": log.role.value,
            "message": log.message,
            "timestamp": log.created_at,
            "emotion": log.emotion,
            "emotion_score": log.emotion_score
        })
    
    return context


async def delete_chat_log(db: AsyncSession, log_id: int) -> bool:
    """채팅 로그 삭제"""
    result = await db.execute(
        select(ChatLog).where(ChatLog.id == log_id)
    )
    chat_log = result.scalar_one_or_none()
    
    if not chat_log:
        return False
    
    await db.delete(chat_log)
    await db.commit()
    return True


async def delete_user_chat_history(
    db: AsyncSession,
    user_id: int,
    days: Optional[int] = None
) -> int:
    """사용자 채팅 히스토리 삭제"""
    query = select(ChatLog).where(ChatLog.user_id == user_id)
    
    if days:
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        query = query.where(ChatLog.created_at < cutoff_date)
    
    result = await db.execute(query)
    logs_to_delete = result.scalars().all()
    
    count = len(logs_to_delete)
    for log in logs_to_delete:
        await db.delete(log)
    
    await db.commit()
    return count


async def get_chat_statistics(db: AsyncSession) -> Dict[str, Any]:
    """전체 채팅 통계"""
    # 총 메시지 수
    total_messages_result = await db.execute(
        select(func.count(ChatLog.id))
    )
    total_messages = total_messages_result.scalar() or 0
    
    # 총 세션 수
    total_sessions_result = await db.execute(
        select(func.count(ChatSession.id))
    )
    total_sessions = total_sessions_result.scalar() or 0
    
    # 활성 사용자 수 (최근 7일)
    recent_cutoff = datetime.utcnow() - timedelta(days=7)
    active_users_result = await db.execute(
        select(func.count(func.distinct(ChatLog.user_id)))
        .where(ChatLog.created_at >= recent_cutoff)
    )
    active_users = active_users_result.scalar() or 0
    
    # 평균 메시지 수
    avg_messages_result = await db.execute(
        select(func.avg(ChatSession.message_count))
        .where(ChatSession.message_count > 0)
    )
    avg_messages = avg_messages_result.scalar() or 0
    
    # 가장 활발한 시간대
    most_active_hour_result = await db.execute(
        select(
            func.extract('hour', ChatLog.created_at).label('hour'),
            func.count(ChatLog.id)
        )
        .group_by('hour')
        .order_by(desc(func.count(ChatLog.id)))
        .limit(1)
    )
    most_active_hour_data = most_active_hour_result.fetchone()
    most_active_hour = int(most_active_hour_data[0]) if most_active_hour_data else 0
    
    return {
        "total_messages": total_messages,
        "total_sessions": total_sessions,
        "active_users": active_users,
        "avg_messages_per_session": round(float(avg_messages), 1) if avg_messages else 0,
        "most_active_hour": most_active_hour
    }


async def bulk_update_vector_ids(
    db: AsyncSession,
    updates: List[Dict[str, Any]]
) -> int:
    """벡터 ID 일괄 업데이트"""
    updated_count = 0
    
    for update in updates:
        log_id = update.get("log_id")
        vector_id = update.get("vector_id")
        
        if log_id and vector_id:
            result = await db.execute(
                select(ChatLog).where(ChatLog.id == log_id)
            )
            chat_log = result.scalar_one_or_none()
            
            if chat_log:
                chat_log.qdrant_vector_id = vector_id
                updated_count += 1
    
    await db.commit()
    return updated_count


# 추가된 함수들 (API에서 사용하는 함수들)

async def get_user_chat_history(
    db: AsyncSession,
    user_id: str,
    limit: int = 50,
    offset: int = 0
) -> List[ChatLog]:
    """사용자 채팅 기록 조회 (문자열 user_id 지원)"""
    query = select(ChatLog).where(ChatLog.user_id == user_id)
    query = query.order_by(desc(ChatLog.created_at))
    query = query.offset(offset).limit(limit)
    
    result = await db.execute(query)
    return result.scalars().all()


async def get_chat_session_history(
    db: AsyncSession,
    user_id: str,
    session_id: str,
    limit: int = 50,
    offset: int = 0
) -> List[ChatLog]:
    """특정 세션의 채팅 기록 조회"""
    query = select(ChatLog).where(
        and_(
            ChatLog.user_id == user_id,
            ChatLog.session_id == session_id
        )
    )
    query = query.order_by(desc(ChatLog.created_at))
    query = query.offset(offset).limit(limit)
    
    result = await db.execute(query)
    return result.scalars().all()


async def get_active_chat_session(
    db: AsyncSession,
    user_id: str
) -> Optional[ChatSession]:
    """사용자의 활성 채팅 세션 조회"""
    result = await db.execute(
        select(ChatSession).where(
            and_(
                ChatSession.user_id == user_id,
                ChatSession.end_time.is_(None)
            )
        ).order_by(desc(ChatSession.start_time))
    )
    return result.scalars().first() 