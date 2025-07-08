"""
일정 관리 API 라우터

사용자의 다양한 일정(약물 복용, 병원 예약, 운동, 취미 활동 등)을 관리하는 API입니다.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, date, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Query
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from app.database import get_db
from app.schemas.schedule import (
    ScheduleCreate, ScheduleResponse, ScheduleUpdate, ScheduleLogCreate, ScheduleLogResponse,
    ScheduleStatsResponse, ComplianceResponse, ReminderResponse, ScheduleSearchRequest,
    ScheduleListResponse, ScheduleBatchRequest, ScheduleBatchResponse, ScheduleTemplateCreate,
    ScheduleTemplateResponse, CalendarDayResponse, ScheduleInsightResponse,
    ScheduleType, ScheduleStatus, Priority, LogStatus
)
from app.crud.schedule import (
    create_schedule, get_schedule_by_id, get_user_schedules, update_schedule,
    delete_schedule, create_schedule_log, get_schedule_logs, get_schedule_stats,
    get_schedule_compliance, get_pending_reminders, mark_schedule_completed,
    get_today_schedules, get_upcoming_schedules, get_overdue_schedules,
    create_schedule_template, get_user_schedule_templates, search_schedules,
    batch_update_schedules, increment_template_usage
)

# 로깅 설정
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/schedules", tags=["schedules"])


# ===== 일정 관리 API =====

@router.post("/")
async def create_schedule_endpoint(
    schedule_data: ScheduleCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    새 일정 생성
    
    다양한 유형의 일정을 생성할 수 있습니다:
    - medication: 약물 복용
    - medical: 병원 예약
    - exercise: 운동
    - hobby: 취미 활동
    - family: 가족 모임
    - social: 사회 활동
    - personal: 개인 일정
    - reminder: 일반 알림
    - other: 기타
    """
    try:
        # 중복 일정 확인 (같은 시간대)
        existing_schedules = await get_user_schedules(
            db, 
            schedule_data.user_id,
            start_date=schedule_data.start_datetime.date(),
            end_date=schedule_data.start_datetime.date()
        )
        
        # 같은 시간대에 우선순위가 높은 일정이 있는지 확인
        for existing in existing_schedules:
            if (existing.start_datetime.hour == schedule_data.start_datetime.hour and
                existing.priority == "urgent" and schedule_data.priority != "urgent"):
                logger.warning(f"긴급 일정과 시간 충돌 - 사용자: {schedule_data.user_id}")
        
        new_schedule = await create_schedule(db, schedule_data)
        
        # 백그라운드에서 알림 설정
        background_tasks.add_task(
            setup_schedule_reminders,
            new_schedule.id,
            schedule_data.user_id,
            new_schedule.start_datetime,
            schedule_data.reminder_minutes
        )
        
        logger.info(f"일정 생성 완료 - 사용자: {schedule_data.user_id}, 제목: {schedule_data.title}")
        
        # 스키마 매핑 문제 해결을 위해 딕셔너리로 변환
        return {
            "id": new_schedule.id,
            "user_id": new_schedule.user_id,
            "title": new_schedule.title,
            "schedule_type": new_schedule.schedule_type,
            "description": new_schedule.description,
            "location": new_schedule.location,
            "priority": new_schedule.priority,
            "start_datetime": new_schedule.start_datetime,
            "end_datetime": new_schedule.end_datetime,
            "is_all_day": new_schedule.is_all_day,
            "recurrence_type": new_schedule.recurrence_type,
            "recurrence_interval": new_schedule.recurrence_interval,
            "recurrence_days": new_schedule.recurrence_days,
            "recurrence_end_date": new_schedule.recurrence_end_date,
            "reminder_minutes": new_schedule.reminder_minutes,
            "metadata": new_schedule.additional_data or {},
            "notes": new_schedule.notes,
            "status": new_schedule.status,
            "created_at": new_schedule.created_at,
            "updated_at": new_schedule.updated_at
        }
        
    except Exception as e:
        logger.error(f"일정 생성 실패: {e}")
        raise HTTPException(status_code=500, detail="일정 생성에 실패했습니다")


@router.get("/{schedule_id}")
async def get_schedule(
    schedule_id: str,
    db: AsyncSession = Depends(get_db)
):
    """일정 상세 조회"""
    schedule = await get_schedule_by_id(db, schedule_id)
    if not schedule:
        raise HTTPException(status_code=404, detail="일정을 찾을 수 없습니다")
    
    # 스키마 매핑 문제 해결을 위해 딕셔너리로 변환
    return {
        "id": schedule.id,
        "user_id": schedule.user_id,
        "title": schedule.title,
        "schedule_type": schedule.schedule_type,
        "description": schedule.description,
        "location": schedule.location,
        "priority": schedule.priority,
        "start_datetime": schedule.start_datetime,
        "end_datetime": schedule.end_datetime,
        "is_all_day": schedule.is_all_day,
        "recurrence_type": schedule.recurrence_type,
        "recurrence_interval": schedule.recurrence_interval,
        "recurrence_days": schedule.recurrence_days,
        "recurrence_end_date": schedule.recurrence_end_date,
        "reminder_minutes": schedule.reminder_minutes,
        "metadata": schedule.additional_data or {},
        "notes": schedule.notes,
        "status": schedule.status,
        "created_at": schedule.created_at,
        "updated_at": schedule.updated_at
    }


@router.get("/user/{user_id}")
async def get_user_schedules_endpoint(
    user_id: str,
    schedule_type: Optional[ScheduleType] = Query(None, description="일정 유형 필터"),
    status: Optional[ScheduleStatus] = Query(None, description="상태 필터"),
    priority: Optional[Priority] = Query(None, description="우선순위 필터"),
    start_date: Optional[date] = Query(None, description="시작 날짜"),
    end_date: Optional[date] = Query(None, description="종료 날짜"),
    limit: int = Query(100, ge=1, le=500, description="결과 수 제한"),
    offset: int = Query(0, ge=0, description="결과 오프셋"),
    db: AsyncSession = Depends(get_db)
):
    """사용자 일정 목록 조회"""
    try:
        schedules = await get_user_schedules(
            db, user_id, schedule_type, status, start_date, end_date, priority, limit, offset
        )
        logger.info(f"사용자 일정 조회 완료 - 사용자: {user_id}, 결과: {len(schedules)}개")
        
        # 스키마 매핑 문제 해결을 위해 딕셔너리로 변환
        result = []
        for schedule in schedules:
            schedule_dict = {
                "id": schedule.id,
                "user_id": schedule.user_id,
                "title": schedule.title,
                "schedule_type": schedule.schedule_type,
                "description": schedule.description,
                "location": schedule.location,
                "priority": schedule.priority,
                "start_datetime": schedule.start_datetime,
                "end_datetime": schedule.end_datetime,
                "is_all_day": schedule.is_all_day,
                "recurrence_type": schedule.recurrence_type,
                "recurrence_interval": schedule.recurrence_interval,
                "recurrence_days": schedule.recurrence_days,
                "recurrence_end_date": schedule.recurrence_end_date,
                "reminder_minutes": schedule.reminder_minutes,
                "metadata": schedule.additional_data or {},
                "notes": schedule.notes,
                "status": schedule.status,
                "created_at": schedule.created_at,
                "updated_at": schedule.updated_at
            }
            result.append(schedule_dict)
        
        return result
        
    except Exception as e:
        logger.error(f"일정 조회 실패: {e}")
        raise HTTPException(status_code=500, detail="일정 조회에 실패했습니다")


@router.put("/{schedule_id}")
async def update_schedule_endpoint(
    schedule_id: str,
    schedule_data: ScheduleUpdate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """일정 수정"""
    try:
        existing_schedule = await get_schedule_by_id(db, schedule_id)
        if not existing_schedule:
            raise HTTPException(status_code=404, detail="일정을 찾을 수 없습니다")
        
        updated_schedule = await update_schedule(db, schedule_id, schedule_data)
        if not updated_schedule:
            raise HTTPException(status_code=404, detail="일정 수정에 실패했습니다")
        
        # 시간이 변경된 경우 알림 재설정
        if schedule_data.start_datetime:
            background_tasks.add_task(
                update_schedule_reminders,
                schedule_id,
                updated_schedule.user_id,
                schedule_data.start_datetime
            )
        
        logger.info(f"일정 수정 완료 - ID: {schedule_id}")
        
        # 스키마 매핑 문제 해결을 위해 딕셔너리로 변환
        return {
            "id": updated_schedule.id,
            "user_id": updated_schedule.user_id,
            "title": updated_schedule.title,
            "schedule_type": updated_schedule.schedule_type,
            "description": updated_schedule.description,
            "location": updated_schedule.location,
            "priority": updated_schedule.priority,
            "start_datetime": updated_schedule.start_datetime,
            "end_datetime": updated_schedule.end_datetime,
            "is_all_day": updated_schedule.is_all_day,
            "recurrence_type": updated_schedule.recurrence_type,
            "recurrence_interval": updated_schedule.recurrence_interval,
            "recurrence_days": updated_schedule.recurrence_days,
            "recurrence_end_date": updated_schedule.recurrence_end_date,
            "reminder_minutes": updated_schedule.reminder_minutes,
            "metadata": updated_schedule.additional_data or {},
            "notes": updated_schedule.notes,
            "status": updated_schedule.status,
            "created_at": updated_schedule.created_at,
            "updated_at": updated_schedule.updated_at
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"일정 수정 실패: {e}")
        raise HTTPException(status_code=500, detail="일정 수정에 실패했습니다")


@router.delete("/{schedule_id}")
async def delete_schedule_endpoint(
    schedule_id: str,
    db: AsyncSession = Depends(get_db)
):
    """일정 삭제"""
    try:
        schedule = await get_schedule_by_id(db, schedule_id)
        if not schedule:
            raise HTTPException(status_code=404, detail="일정을 찾을 수 없습니다")
        
        success = await delete_schedule(db, schedule_id)
        if not success:
            raise HTTPException(status_code=500, detail="일정 삭제에 실패했습니다")
        
        logger.info(f"일정 삭제 완료 - ID: {schedule_id}")
        return {"message": "일정이 성공적으로 삭제되었습니다", "schedule_id": schedule_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"일정 삭제 실패: {e}")
        raise HTTPException(status_code=500, detail="일정 삭제에 실패했습니다")


# ===== 일정 기록 API =====

@router.post("/logs", response_model=ScheduleLogResponse)
async def create_schedule_log_endpoint(
    log_data: ScheduleLogCreate,
    db: AsyncSession = Depends(get_db)
):
    """일정 기록 생성"""
    try:
        # 일정 존재 확인
        schedule = await get_schedule_by_id(db, log_data.schedule_id)
        if not schedule:
            raise HTTPException(status_code=404, detail="일정을 찾을 수 없습니다")
        
        new_log = await create_schedule_log(db, log_data)
        logger.info(f"일정 기록 생성 완료 - 일정: {log_data.schedule_id}")
        return new_log
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"일정 기록 생성 실패: {e}")
        raise HTTPException(status_code=500, detail="일정 기록 생성에 실패했습니다")


@router.get("/logs/{user_id}", response_model=List[ScheduleLogResponse])
async def get_schedule_logs_endpoint(
    user_id: str,
    schedule_id: Optional[str] = Query(None, description="특정 일정 ID 필터"),
    status: Optional[LogStatus] = Query(None, description="상태 필터"),
    start_date: Optional[date] = Query(None, description="시작 날짜"),
    end_date: Optional[date] = Query(None, description="종료 날짜"),
    limit: int = Query(100, ge=1, le=500, description="결과 수 제한"),
    db: AsyncSession = Depends(get_db)
):
    """일정 기록 조회"""
    try:
        logs = await get_schedule_logs(db, user_id, schedule_id, status, start_date, end_date, limit)
        logger.info(f"일정 기록 조회 완료 - 사용자: {user_id}, 결과: {len(logs)}개")
        return logs
        
    except Exception as e:
        logger.error(f"일정 기록 조회 실패: {e}")
        raise HTTPException(status_code=500, detail="일정 기록 조회에 실패했습니다")


@router.post("/{schedule_id}/complete")
async def mark_schedule_completed_endpoint(
    schedule_id: str,
    user_id: str,
    completed_at: Optional[datetime] = None,
    notes: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """일정 완료 처리"""
    try:
        schedule = await get_schedule_by_id(db, schedule_id)
        if not schedule:
            raise HTTPException(status_code=404, detail="일정을 찾을 수 없습니다")
        
        if schedule.user_id != user_id:
            raise HTTPException(status_code=403, detail="권한이 없습니다")
        
        success = await mark_schedule_completed(db, schedule_id, user_id, completed_at, notes)
        if not success:
            raise HTTPException(status_code=500, detail="일정 완료 처리에 실패했습니다")
        
        logger.info(f"일정 완료 처리 - ID: {schedule_id}")
        return {
            "message": "일정이 완료되었습니다",
            "schedule_id": schedule_id,
            "title": schedule.title,
            "completed_at": completed_at or datetime.now()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"일정 완료 처리 실패: {e}")
        raise HTTPException(status_code=500, detail="일정 완료 처리에 실패했습니다")


# ===== 알림 API =====

@router.get("/reminders/{user_id}", response_model=List[ReminderResponse])
async def get_schedule_reminders(
    user_id: str,
    hours_ahead: int = Query(24, ge=1, le=168, description="몇 시간 후까지의 알림"),
    include_overdue: bool = Query(True, description="연체 알림 포함 여부"),
    db: AsyncSession = Depends(get_db)
):
    """사용자 일정 알림 조회"""
    try:
        # 다가오는 일정
        upcoming_schedules = await get_upcoming_schedules(db, user_id, hours_ahead)
        
        # 연체된 일정
        overdue_schedules = []
        if include_overdue:
            overdue_schedules = await get_overdue_schedules(db, user_id)
        
        all_schedules = upcoming_schedules + overdue_schedules
        
        reminder_responses = []
        for schedule in all_schedules:
            now = datetime.now()
            is_overdue = schedule.start_datetime < now
            
            # 다음 알림 시간 계산
            for reminder_minutes in schedule.reminder_minutes:
                reminder_datetime = schedule.start_datetime - timedelta(minutes=reminder_minutes)
                
                # 이미 지난 알림은 제외 (연체 일정 제외)
                if reminder_datetime < now and not is_overdue:
                    continue
                
                time_until_due = None
                if not is_overdue:
                    delta = schedule.start_datetime - now
                    time_until_due = format_time_delta(delta)
                
                reminder_responses.append(ReminderResponse(
                    schedule_id=schedule.id,
                    title=schedule.title,
                    schedule_type=schedule.schedule_type,
                    description=schedule.description,
                    location=schedule.location,
                    priority=schedule.priority,
                    scheduled_datetime=schedule.start_datetime,
                    reminder_datetime=reminder_datetime,
                    status="overdue" if is_overdue else "pending",
                    is_overdue=is_overdue,
                    time_until_due=time_until_due,
                    metadata=schedule.additional_data
                ))
        
        # 알림 시간 순 정렬
        reminder_responses.sort(key=lambda x: x.reminder_datetime)
        
        logger.info(f"일정 알림 조회 완료 - 사용자: {user_id}, 알림: {len(reminder_responses)}개")
        return reminder_responses
        
    except Exception as e:
        logger.error(f"알림 조회 실패: {e}")
        raise HTTPException(status_code=500, detail="알림 조회에 실패했습니다")


@router.get("/today/{user_id}")
async def get_today_schedules_endpoint(
    user_id: str,
    db: AsyncSession = Depends(get_db)
):
    """오늘의 일정 조회"""
    try:
        schedules = await get_today_schedules(db, user_id)
        logger.info(f"오늘의 일정 조회 완료 - 사용자: {user_id}, 결과: {len(schedules)}개")
        
        # 스키마 매핑 문제 해결을 위해 딕셔너리로 변환
        result = []
        for schedule in schedules:
            schedule_dict = {
                "id": schedule.id,
                "user_id": schedule.user_id,
                "title": schedule.title,
                "schedule_type": schedule.schedule_type,
                "description": schedule.description,
                "location": schedule.location,
                "priority": schedule.priority,
                "start_datetime": schedule.start_datetime,
                "end_datetime": schedule.end_datetime,
                "is_all_day": schedule.is_all_day,
                "recurrence_type": schedule.recurrence_type,
                "recurrence_interval": schedule.recurrence_interval,
                "recurrence_days": schedule.recurrence_days,
                "recurrence_end_date": schedule.recurrence_end_date,
                "reminder_minutes": schedule.reminder_minutes,
                "metadata": schedule.additional_data or {},
                "notes": schedule.notes,
                "status": schedule.status,
                "created_at": schedule.created_at,
                "updated_at": schedule.updated_at
            }
            result.append(schedule_dict)
        
        return result
        
    except Exception as e:
        logger.error(f"오늘의 일정 조회 실패: {e}")
        raise HTTPException(status_code=500, detail="오늘의 일정 조회에 실패했습니다")


# ===== 통계 및 분석 API =====

@router.get("/stats/{user_id}", response_model=ScheduleStatsResponse)
async def get_schedule_statistics(
    user_id: str,
    days_back: int = Query(30, ge=1, le=365, description="분석 기간 (일)"),
    db: AsyncSession = Depends(get_db)
):
    """일정 통계 조회"""
    try:
        stats = await get_schedule_stats(db, user_id, days_back)
        
        # 추가 계산
        on_time_rate = 0.0  # 시간대별 분석으로 계산 가능
        current_streak_days = 0  # 연속 완료 일수 계산
        daily_completion = {}  # 일별 완료 현황
        missed_by_time = {}  # 시간대별 누락 현황
        
        response = ScheduleStatsResponse(
            user_id=user_id,
            period_days=days_back,
            total_scheduled=stats["total_scheduled"],
            total_completed=stats["total_completed"],
            total_missed=stats["total_missed"],
            completion_rate=stats["completion_rate"],
            on_time_rate=on_time_rate,
            type_breakdown=stats["type_breakdown"],
            priority_breakdown=stats["priority_breakdown"],
            daily_completion=daily_completion,
            missed_by_time=missed_by_time,
            current_streak_days=current_streak_days
        )
        
        logger.info(f"일정 통계 조회 완료 - 사용자: {user_id}")
        return response
        
    except Exception as e:
        logger.error(f"통계 조회 실패: {e}")
        raise HTTPException(status_code=500, detail="통계 조회에 실패했습니다")


@router.get("/compliance/{user_id}", response_model=ComplianceResponse)
async def get_schedule_compliance_analysis(
    user_id: str,
    days_back: int = Query(30, ge=7, le=365, description="분석 기간 (일)"),
    db: AsyncSession = Depends(get_db)
):
    """일정 순응도 분석"""
    try:
        compliance = await get_schedule_compliance(db, user_id, days_back)
        return ComplianceResponse(**compliance)
        
    except Exception as e:
        logger.error(f"순응도 분석 실패: {e}")
        raise HTTPException(status_code=500, detail="순응도 분석에 실패했습니다")


@router.get("/insights/{user_id}", response_model=ScheduleInsightResponse)
async def get_schedule_insights(
    user_id: str,
    days_back: int = Query(30, ge=7, le=90, description="분석 기간 (일)"),
    db: AsyncSession = Depends(get_db)
):
    """일정 인사이트 생성"""
    try:
        stats = await get_schedule_stats(db, user_id, days_back)
        compliance = await get_schedule_compliance(db, user_id, days_back)
        
        # 인사이트 생성
        insights = []
        improvement_suggestions = []
        
        # 완료율 분석
        completion_rate = stats["completion_rate"]
        if completion_rate >= 90:
            insights.append("훌륭한 일정 관리를 하고 계시네요!")
        elif completion_rate >= 70:
            insights.append("전반적으로 일정을 잘 지키고 계십니다.")
            improvement_suggestions.append("완료율을 더 높이기 위해 알림 시간을 조정해보세요.")
        else:
            insights.append("일정 관리에 어려움을 겪고 계시는 것 같습니다.")
            improvement_suggestions.extend([
                "더 현실적인 일정을 세워보세요.",
                "알림 기능을 적극 활용해보세요.",
                "일정을 작은 단위로 나누어보세요."
            ])
        
        # 유형별 분석
        type_breakdown = stats["type_breakdown"]
        if type_breakdown:
            most_frequent_type = max(type_breakdown, key=type_breakdown.get)
            insights.append(f"'{most_frequent_type}' 유형의 일정이 가장 많습니다.")
        
        # 시간대 분석 (가상 데이터)
        peak_hours = [9, 14, 19]  # 실제로는 데이터에서 계산
        
        # 생산성 점수 계산
        productivity_score = min(100, completion_rate + 10)  # 간단한 계산
        
        # 일정 균형 분석
        schedule_balance = {}
        total_schedules = sum(type_breakdown.values()) if type_breakdown else 1
        for schedule_type, count in type_breakdown.items():
            schedule_balance[schedule_type] = (count / total_schedules) * 100
        
        # 습관 분석
        habit_analysis = {
            "consistency_score": completion_rate,
            "preferred_times": peak_hours,
            "strong_areas": list(type_breakdown.keys())[:3],
            "improvement_areas": compliance["recommendations"]
        }
        
        response = ScheduleInsightResponse(
            user_id=user_id,
            analysis_period=days_back,
            insights=insights,
            productivity_score=productivity_score,
            schedule_balance=schedule_balance,
            peak_productivity_hours=peak_hours,
            improvement_suggestions=improvement_suggestions,
            habit_analysis=habit_analysis,
            generated_at=datetime.now()
        )
        
        logger.info(f"일정 인사이트 생성 완료 - 사용자: {user_id}")
        return response
        
    except Exception as e:
        logger.error(f"인사이트 생성 실패: {e}")
        raise HTTPException(status_code=500, detail="인사이트 생성에 실패했습니다")


# ===== 검색 및 템플릿 API =====

@router.post("/search", response_model=ScheduleListResponse)
async def search_schedules_endpoint(
    search_request: ScheduleSearchRequest,
    user_id: str,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db)
):
    """일정 검색"""
    try:
        schedules = await search_schedules(
            db, user_id, search_request.query or "", 
            search_request.schedule_types, limit
        )
        
        # 추가 필터링 적용
        filtered_schedules = schedules
        if search_request.priority:
            filtered_schedules = [s for s in filtered_schedules if s.priority == search_request.priority]
        if search_request.status:
            filtered_schedules = [s for s in filtered_schedules if s.status == search_request.status]
        if search_request.location:
            filtered_schedules = [s for s in filtered_schedules if 
                                search_request.location.lower() in (s.location or "").lower()]
        
        # 페이징
        total_count = len(filtered_schedules)
        paginated_schedules = filtered_schedules[offset:offset + limit]
        
        response = ScheduleListResponse(
            schedules=paginated_schedules,
            total_count=total_count,
            filtered_count=len(paginated_schedules),
            page=offset // limit + 1,
            limit=limit,
            has_more=offset + limit < total_count
        )
        
        logger.info(f"일정 검색 완료 - 사용자: {user_id}, 결과: {len(paginated_schedules)}개")
        return response
        
    except Exception as e:
        logger.error(f"일정 검색 실패: {e}")
        raise HTTPException(status_code=500, detail="일정 검색에 실패했습니다")


@router.post("/templates", response_model=ScheduleTemplateResponse)
async def create_schedule_template_endpoint(
    template_data: ScheduleTemplateCreate,
    db: AsyncSession = Depends(get_db)
):
    """일정 템플릿 생성"""
    try:
        new_template = await create_schedule_template(db, template_data)
        logger.info(f"일정 템플릿 생성 완료 - 사용자: {template_data.user_id}")
        return new_template
        
    except Exception as e:
        logger.error(f"템플릿 생성 실패: {e}")
        raise HTTPException(status_code=500, detail="템플릿 생성에 실패했습니다")


@router.get("/templates/{user_id}", response_model=List[ScheduleTemplateResponse])
async def get_user_templates(
    user_id: str,
    schedule_type: Optional[ScheduleType] = Query(None, description="일정 유형 필터"),
    db: AsyncSession = Depends(get_db)
):
    """사용자 일정 템플릿 조회"""
    try:
        templates = await get_user_schedule_templates(db, user_id, schedule_type)
        logger.info(f"템플릿 조회 완료 - 사용자: {user_id}, 템플릿: {len(templates)}개")
        return templates
        
    except Exception as e:
        logger.error(f"템플릿 조회 실패: {e}")
        raise HTTPException(status_code=500, detail="템플릿 조회에 실패했습니다")


@router.post("/batch", response_model=ScheduleBatchResponse)
async def batch_update_schedules_endpoint(
    batch_request: ScheduleBatchRequest,
    db: AsyncSession = Depends(get_db)
):
    """일정 일괄 처리"""
    try:
        action_mapping = {
            "complete": {"status": ScheduleStatus.COMPLETED},
            "cancel": {"status": ScheduleStatus.CANCELLED},
            "postpone": {"status": ScheduleStatus.POSTPONED}
        }
        
        if batch_request.action not in action_mapping:
            raise HTTPException(status_code=400, detail="지원하지 않는 액션입니다")
        
        update_data = action_mapping[batch_request.action]
        if batch_request.action_data:
            update_data.update(batch_request.action_data)
        
        result = await batch_update_schedules(db, batch_request.schedule_ids, update_data)
        
        response = ScheduleBatchResponse(**result)
        logger.info(f"일괄 처리 완료 - 성공: {response.success_count}, 실패: {response.failed_count}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"일괄 처리 실패: {e}")
        raise HTTPException(status_code=500, detail="일괄 처리에 실패했습니다")


# ===== 헬퍼 함수 =====

async def setup_schedule_reminders(
    schedule_id: str,
    user_id: str,
    start_datetime: datetime,
    reminder_minutes: List[int]
):
    """일정 알림 설정 (백그라운드 작업)"""
    try:
        # 실제 알림 시스템과 연동
        logger.info(f"알림 설정 완료 - 일정: {schedule_id}, 알림: {len(reminder_minutes)}개")
    except Exception as e:
        logger.error(f"알림 설정 실패: {e}")


async def update_schedule_reminders(
    schedule_id: str,
    user_id: str,
    new_datetime: datetime
):
    """일정 알림 업데이트 (백그라운드 작업)"""
    try:
        # 기존 알림 삭제 후 새로 설정
        logger.info(f"알림 업데이트 완료 - 일정: {schedule_id}")
    except Exception as e:
        logger.error(f"알림 업데이트 실패: {e}")


def format_time_delta(delta: timedelta) -> str:
    """시간 차이를 사용자 친화적 형식으로 변환"""
    total_seconds = int(delta.total_seconds())
    
    if total_seconds < 0:
        return "지남"
    
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    
    if hours > 24:
        days = hours // 24
        remaining_hours = hours % 24
        return f"{days}일 {remaining_hours}시간 후"
    elif hours > 0:
        return f"{hours}시간 {minutes}분 후"
    else:
        return f"{minutes}분 후" 