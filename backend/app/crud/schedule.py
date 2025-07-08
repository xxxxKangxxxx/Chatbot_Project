"""
일정 관리 CRUD 연산

사용자의 다양한 일정(약물 복용, 병원 예약, 운동, 취미 활동 등)에 대한 
데이터베이스 연산을 처리합니다.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, date, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc, asc
from sqlalchemy.orm import selectinload
import uuid

from app.models.schedule import Schedule, ScheduleLog, ScheduleTemplate, Reminder, ScheduleStats
from app.schemas.schedule import (
    ScheduleCreate, ScheduleUpdate, ScheduleLogCreate, ScheduleLogUpdate,
    ScheduleTemplateCreate, ScheduleType, ScheduleStatus, LogStatus, Priority
)


# ===== 일정 관리 CRUD =====

async def create_schedule(db: AsyncSession, schedule_data: ScheduleCreate) -> Schedule:
    """새 일정 생성"""
    schedule_dict = schedule_data.dict()
    schedule_dict['id'] = str(uuid.uuid4())
    
    # 스키마의 metadata 필드를 모델의 additional_data 필드로 매핑
    if 'metadata' in schedule_dict:
        schedule_dict['additional_data'] = schedule_dict.pop('metadata')
    
    new_schedule = Schedule(**schedule_dict)
    db.add(new_schedule)
    await db.commit()
    await db.refresh(new_schedule)
    return new_schedule


async def get_schedule_by_id(db: AsyncSession, schedule_id: str) -> Optional[Schedule]:
    """ID로 일정 조회"""
    result = await db.execute(
        select(Schedule)
        .options(selectinload(Schedule.schedule_logs))
        .where(Schedule.id == schedule_id)
    )
    return result.scalar_one_or_none()


async def get_user_schedules(
    db: AsyncSession,
    user_id: str,
    schedule_type: Optional[ScheduleType] = None,
    status: Optional[ScheduleStatus] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    priority: Optional[Priority] = None,
    limit: int = 100,
    offset: int = 0
) -> List[Schedule]:
    """사용자 일정 목록 조회"""
    query = select(Schedule).where(Schedule.user_id == user_id)
    
    # 필터 적용
    if schedule_type:
        query = query.where(Schedule.schedule_type == schedule_type)
    if status:
        query = query.where(Schedule.status == status)
    if priority:
        query = query.where(Schedule.priority == priority)
    if start_date:
        query = query.where(func.date(Schedule.start_datetime) >= start_date)
    if end_date:
        query = query.where(func.date(Schedule.start_datetime) <= end_date)
    
    query = query.order_by(Schedule.start_datetime).limit(limit).offset(offset)
    
    result = await db.execute(query)
    return result.scalars().all()


async def update_schedule(
    db: AsyncSession, 
    schedule_id: str, 
    schedule_data: ScheduleUpdate
) -> Optional[Schedule]:
    """일정 수정"""
    result = await db.execute(select(Schedule).where(Schedule.id == schedule_id))
    schedule = result.scalar_one_or_none()
    
    if not schedule:
        return None
    
    update_data = schedule_data.dict(exclude_unset=True)
    
    # 스키마의 metadata 필드를 모델의 additional_data 필드로 매핑
    if 'metadata' in update_data:
        update_data['additional_data'] = update_data.pop('metadata')
    
    for field, value in update_data.items():
        setattr(schedule, field, value)
    
    await db.commit()
    await db.refresh(schedule)
    return schedule


async def delete_schedule(db: AsyncSession, schedule_id: str) -> bool:
    """일정 삭제"""
    result = await db.execute(select(Schedule).where(Schedule.id == schedule_id))
    schedule = result.scalar_one_or_none()
    
    if not schedule:
        return False
    
    await db.delete(schedule)
    await db.commit()
    return True


async def get_schedules_by_date_range(
    db: AsyncSession,
    user_id: str,
    start_date: datetime,
    end_date: datetime
) -> List[Schedule]:
    """날짜 범위로 일정 조회"""
    result = await db.execute(
        select(Schedule)
        .where(
            and_(
                Schedule.user_id == user_id,
                Schedule.start_datetime >= start_date,
                Schedule.start_datetime <= end_date
            )
        )
        .order_by(Schedule.start_datetime)
    )
    return result.scalars().all()


async def get_today_schedules(db: AsyncSession, user_id: str) -> List[Schedule]:
    """오늘의 일정 조회"""
    today = date.today()
    start_datetime = datetime.combine(today, datetime.min.time())
    end_datetime = datetime.combine(today, datetime.max.time())
    
    return await get_schedules_by_date_range(db, user_id, start_datetime, end_datetime)


async def get_upcoming_schedules(
    db: AsyncSession, 
    user_id: str, 
    hours: int = 24
) -> List[Schedule]:
    """다가오는 일정 조회"""
    now = datetime.now()
    future_time = now + timedelta(hours=hours)
    
    result = await db.execute(
        select(Schedule)
        .where(
            and_(
                Schedule.user_id == user_id,
                Schedule.start_datetime >= now,
                Schedule.start_datetime <= future_time,
                Schedule.status == ScheduleStatus.ACTIVE
            )
        )
        .order_by(Schedule.start_datetime)
    )
    return result.scalars().all()


async def get_overdue_schedules(db: AsyncSession, user_id: str) -> List[Schedule]:
    """연체된 일정 조회"""
    now = datetime.now()
    
    result = await db.execute(
        select(Schedule)
        .where(
            and_(
                Schedule.user_id == user_id,
                Schedule.start_datetime < now,
                Schedule.status == ScheduleStatus.ACTIVE
            )
        )
        .order_by(Schedule.start_datetime)
    )
    return result.scalars().all()


# ===== 일정 기록 CRUD =====

async def create_schedule_log(db: AsyncSession, log_data: ScheduleLogCreate) -> ScheduleLog:
    """일정 기록 생성"""
    log_dict = log_data.dict()
    log_dict['id'] = str(uuid.uuid4())
    
    new_log = ScheduleLog(**log_dict)
    db.add(new_log)
    await db.commit()
    await db.refresh(new_log)
    return new_log


async def get_schedule_logs(
    db: AsyncSession,
    user_id: str,
    schedule_id: Optional[str] = None,
    status: Optional[LogStatus] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    limit: int = 100
) -> List[ScheduleLog]:
    """일정 기록 조회"""
    query = select(ScheduleLog).where(ScheduleLog.user_id == user_id)
    
    if schedule_id:
        query = query.where(ScheduleLog.schedule_id == schedule_id)
    if status:
        query = query.where(ScheduleLog.status == status)
    if start_date:
        query = query.where(func.date(ScheduleLog.scheduled_datetime) >= start_date)
    if end_date:
        query = query.where(func.date(ScheduleLog.scheduled_datetime) <= end_date)
    
    query = query.order_by(desc(ScheduleLog.scheduled_datetime)).limit(limit)
    
    result = await db.execute(query)
    return result.scalars().all()


async def update_schedule_log(
    db: AsyncSession,
    log_id: str,
    log_data: ScheduleLogUpdate
) -> Optional[ScheduleLog]:
    """일정 기록 수정"""
    result = await db.execute(select(ScheduleLog).where(ScheduleLog.id == log_id))
    log = result.scalar_one_or_none()
    
    if not log:
        return None
    
    update_data = log_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(log, field, value)
    
    await db.commit()
    await db.refresh(log)
    return log


async def mark_schedule_completed(
    db: AsyncSession,
    schedule_id: str,
    user_id: str,
    completed_at: Optional[datetime] = None,
    notes: Optional[str] = None
) -> bool:
    """일정 완료 처리"""
    if completed_at is None:
        completed_at = datetime.now()
    
    # 일정 기록 생성
    log_data = ScheduleLogCreate(
        user_id=user_id,
        schedule_id=schedule_id,
        scheduled_datetime=completed_at,
        status=LogStatus.COMPLETED,
        completed_at=completed_at,
        notes=notes
    )
    
    await create_schedule_log(db, log_data)
    
    # 반복 일정이 아닌 경우 상태 변경
    schedule = await get_schedule_by_id(db, schedule_id)
    if schedule and schedule.recurrence_type == "none":
        schedule.status = ScheduleStatus.COMPLETED
        await db.commit()
    
    return True


# ===== 일정 템플릿 CRUD =====

async def create_schedule_template(
    db: AsyncSession, 
    template_data: ScheduleTemplateCreate
) -> ScheduleTemplate:
    """일정 템플릿 생성"""
    template_dict = template_data.dict()
    template_dict['id'] = str(uuid.uuid4())
    
    new_template = ScheduleTemplate(**template_dict)
    db.add(new_template)
    await db.commit()
    await db.refresh(new_template)
    return new_template


async def get_user_schedule_templates(
    db: AsyncSession,
    user_id: str,
    schedule_type: Optional[ScheduleType] = None
) -> List[ScheduleTemplate]:
    """사용자 일정 템플릿 조회"""
    query = select(ScheduleTemplate).where(ScheduleTemplate.user_id == user_id)
    
    if schedule_type:
        query = query.where(ScheduleTemplate.schedule_type == schedule_type)
    
    query = query.order_by(desc(ScheduleTemplate.usage_count), ScheduleTemplate.name)
    
    result = await db.execute(query)
    return result.scalars().all()


async def increment_template_usage(db: AsyncSession, template_id: str) -> bool:
    """템플릿 사용 횟수 증가"""
    result = await db.execute(
        select(ScheduleTemplate).where(ScheduleTemplate.id == template_id)
    )
    template = result.scalar_one_or_none()
    
    if not template:
        return False
    
    template.usage_count += 1
    await db.commit()
    return True


# ===== 알림 관리 CRUD =====

async def create_reminder(
    db: AsyncSession,
    schedule_id: str,
    user_id: str,
    reminder_datetime: datetime,
    message: Optional[str] = None
) -> Reminder:
    """알림 생성"""
    reminder_data = {
        'id': str(uuid.uuid4()),
        'user_id': user_id,
        'schedule_id': schedule_id,
        'reminder_datetime': reminder_datetime,
        'message': message
    }
    
    new_reminder = Reminder(**reminder_data)
    db.add(new_reminder)
    await db.commit()
    await db.refresh(new_reminder)
    return new_reminder


async def get_pending_reminders(
    db: AsyncSession,
    user_id: Optional[str] = None,
    before_datetime: Optional[datetime] = None
) -> List[Reminder]:
    """대기 중인 알림 조회"""
    query = select(Reminder).where(Reminder.is_sent == False)
    
    if user_id:
        query = query.where(Reminder.user_id == user_id)
    if before_datetime:
        query = query.where(Reminder.reminder_datetime <= before_datetime)
    
    query = query.order_by(Reminder.reminder_datetime)
    
    result = await db.execute(query)
    return result.scalars().all()


async def mark_reminder_sent(db: AsyncSession, reminder_id: str) -> bool:
    """알림 발송 완료 처리"""
    result = await db.execute(select(Reminder).where(Reminder.id == reminder_id))
    reminder = result.scalar_one_or_none()
    
    if not reminder:
        return False
    
    reminder.is_sent = True
    reminder.sent_at = datetime.now()
    await db.commit()
    return True


# ===== 통계 및 분석 =====

async def get_schedule_stats(
    db: AsyncSession,
    user_id: str,
    days_back: int = 30
) -> Dict[str, Any]:
    """일정 통계 조회"""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days_back)
    
    # 기본 통계
    total_scheduled_result = await db.execute(
        select(func.count(Schedule.id))
        .where(
            and_(
                Schedule.user_id == user_id,
                Schedule.start_datetime >= start_date,
                Schedule.start_datetime <= end_date
            )
        )
    )
    total_scheduled = total_scheduled_result.scalar() or 0
    
    # 완료된 일정
    completed_logs_result = await db.execute(
        select(func.count(ScheduleLog.id))
        .where(
            and_(
                ScheduleLog.user_id == user_id,
                ScheduleLog.status == LogStatus.COMPLETED,
                ScheduleLog.scheduled_datetime >= start_date,
                ScheduleLog.scheduled_datetime <= end_date
            )
        )
    )
    total_completed = completed_logs_result.scalar() or 0
    
    # 놓친 일정
    missed_logs_result = await db.execute(
        select(func.count(ScheduleLog.id))
        .where(
            and_(
                ScheduleLog.user_id == user_id,
                ScheduleLog.status == LogStatus.MISSED,
                ScheduleLog.scheduled_datetime >= start_date,
                ScheduleLog.scheduled_datetime <= end_date
            )
        )
    )
    total_missed = missed_logs_result.scalar() or 0
    
    # 완료율 계산
    completion_rate = (total_completed / total_scheduled * 100) if total_scheduled > 0 else 0
    
    # 유형별 분류
    type_breakdown_result = await db.execute(
        select(
            Schedule.schedule_type,
            func.count(Schedule.id)
        )
        .where(
            and_(
                Schedule.user_id == user_id,
                Schedule.start_datetime >= start_date,
                Schedule.start_datetime <= end_date
            )
        )
        .group_by(Schedule.schedule_type)
    )
    type_breakdown = dict(type_breakdown_result.fetchall())
    
    # 우선순위별 분류
    priority_breakdown_result = await db.execute(
        select(
            Schedule.priority,
            func.count(Schedule.id)
        )
        .where(
            and_(
                Schedule.user_id == user_id,
                Schedule.start_datetime >= start_date,
                Schedule.start_datetime <= end_date
            )
        )
        .group_by(Schedule.priority)
    )
    priority_breakdown = dict(priority_breakdown_result.fetchall())
    
    return {
        "user_id": user_id,
        "period_days": days_back,
        "total_scheduled": total_scheduled,
        "total_completed": total_completed,
        "total_missed": total_missed,
        "completion_rate": round(completion_rate, 2),
        "type_breakdown": type_breakdown,
        "priority_breakdown": priority_breakdown
    }


async def get_schedule_compliance(
    db: AsyncSession,
    user_id: str,
    days_back: int = 30
) -> Dict[str, Any]:
    """일정 순응도 분석"""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days_back)
    
    # 전체 순응도
    stats = await get_schedule_stats(db, user_id, days_back)
    overall_completion_rate = stats["completion_rate"]
    
    # 유형별 순응도
    type_compliance = {}
    for schedule_type in ScheduleType:
        type_logs_result = await db.execute(
            select(func.count(ScheduleLog.id))
            .join(Schedule, ScheduleLog.schedule_id == Schedule.id)
            .where(
                and_(
                    ScheduleLog.user_id == user_id,
                    Schedule.schedule_type == schedule_type,
                    ScheduleLog.scheduled_datetime >= start_date,
                    ScheduleLog.scheduled_datetime <= end_date
                )
            )
        )
        total_type_logs = type_logs_result.scalar() or 0
        
        completed_type_logs_result = await db.execute(
            select(func.count(ScheduleLog.id))
            .join(Schedule, ScheduleLog.schedule_id == Schedule.id)
            .where(
                and_(
                    ScheduleLog.user_id == user_id,
                    Schedule.schedule_type == schedule_type,
                    ScheduleLog.status == LogStatus.COMPLETED,
                    ScheduleLog.scheduled_datetime >= start_date,
                    ScheduleLog.scheduled_datetime <= end_date
                )
            )
        )
        completed_type_logs = completed_type_logs_result.scalar() or 0
        
        type_compliance[schedule_type] = (
            (completed_type_logs / total_type_logs * 100) 
            if total_type_logs > 0 else 0
        )
    
    # 시간대별 순응도
    time_compliance = {}
    for hour in range(24):
        hour_logs_result = await db.execute(
            select(func.count(ScheduleLog.id))
            .where(
                and_(
                    ScheduleLog.user_id == user_id,
                    func.extract('hour', ScheduleLog.scheduled_datetime) == hour,
                    ScheduleLog.scheduled_datetime >= start_date,
                    ScheduleLog.scheduled_datetime <= end_date
                )
            )
        )
        total_hour_logs = hour_logs_result.scalar() or 0
        
        completed_hour_logs_result = await db.execute(
            select(func.count(ScheduleLog.id))
            .where(
                and_(
                    ScheduleLog.user_id == user_id,
                    ScheduleLog.status == LogStatus.COMPLETED,
                    func.extract('hour', ScheduleLog.scheduled_datetime) == hour,
                    ScheduleLog.scheduled_datetime >= start_date,
                    ScheduleLog.scheduled_datetime <= end_date
                )
            )
        )
        completed_hour_logs = completed_hour_logs_result.scalar() or 0
        
        time_compliance[f"{hour:02d}:00"] = (
            (completed_hour_logs / total_hour_logs * 100) 
            if total_hour_logs > 0 else 0
        )
    
    # 트렌드 분석
    compliance_trend = "stable"
    if overall_completion_rate >= 80:
        compliance_trend = "excellent"
    elif overall_completion_rate >= 60:
        compliance_trend = "good"
    elif overall_completion_rate >= 40:
        compliance_trend = "needs_improvement"
    else:
        compliance_trend = "poor"
    
    # 권장사항
    recommendations = []
    if overall_completion_rate < 70:
        recommendations.append("알림 시간을 조정해보세요")
        recommendations.append("더 작은 단위로 일정을 나누어보세요")
    
    # 위험도 평가
    risk_level = "low"
    if overall_completion_rate < 50:
        risk_level = "high"
    elif overall_completion_rate < 70:
        risk_level = "medium"
    
    return {
        "user_id": user_id,
        "analysis_period_days": days_back,
        "overall_completion_rate": round(overall_completion_rate, 2),
        "type_compliance": {k.value: round(v, 2) for k, v in type_compliance.items()},
        "time_compliance": {k: round(v, 2) for k, v in time_compliance.items()},
        "compliance_trend": compliance_trend,
        "recommendations": recommendations,
        "risk_level": risk_level,
        "last_updated": datetime.now()
    }


async def search_schedules(
    db: AsyncSession,
    user_id: str,
    query: str,
    schedule_types: Optional[List[ScheduleType]] = None,
    limit: int = 50
) -> List[Schedule]:
    """일정 검색"""
    db_query = select(Schedule).where(Schedule.user_id == user_id)
    
    # 텍스트 검색
    if query:
        db_query = db_query.where(
            or_(
                Schedule.title.ilike(f"%{query}%"),
                Schedule.description.ilike(f"%{query}%"),
                Schedule.location.ilike(f"%{query}%"),
                Schedule.notes.ilike(f"%{query}%")
            )
        )
    
    # 유형 필터
    if schedule_types:
        db_query = db_query.where(Schedule.schedule_type.in_([t.value for t in schedule_types]))
    
    db_query = db_query.order_by(Schedule.start_datetime).limit(limit)
    
    result = await db.execute(db_query)
    return result.scalars().all()


async def batch_update_schedules(
    db: AsyncSession,
    schedule_ids: List[str],
    update_data: Dict[str, Any]
) -> Dict[str, Any]:
    """일정 일괄 수정"""
    success_ids = []
    failed_ids = []
    errors = []
    
    for schedule_id in schedule_ids:
        try:
            result = await db.execute(select(Schedule).where(Schedule.id == schedule_id))
            schedule = result.scalar_one_or_none()
            
            if not schedule:
                failed_ids.append(schedule_id)
                errors.append(f"Schedule {schedule_id} not found")
                continue
            
            for field, value in update_data.items():
                if hasattr(schedule, field):
                    setattr(schedule, field, value)
            
            success_ids.append(schedule_id)
            
        except Exception as e:
            failed_ids.append(schedule_id)
            errors.append(f"Error updating {schedule_id}: {str(e)}")
    
    if success_ids:
        await db.commit()
    
    return {
        "success_count": len(success_ids),
        "failed_count": len(failed_ids),
        "total_count": len(schedule_ids),
        "success_ids": success_ids,
        "failed_ids": failed_ids,
        "errors": errors
    } 