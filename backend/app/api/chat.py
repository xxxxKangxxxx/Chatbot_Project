"""
채팅 API 라우터

사용자와의 대화를 처리하는 핵심 API입니다.
임베딩 생성 → Qdrant 저장/검색 → 감정 분석 → GPT 응답 생성 → 저장의 전체 플로우를 담당합니다.
"""

from typing import List, Dict, Any, Optional
import logging
import uuid
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.schemas.chat import (
    ChatRequest, ChatResponse, ChatHistoryResponse, ChatSessionRequest,
    ChatSessionResponse, ChatSessionCreate, ChatPromptContext, ChatVectorPayload
)
from app.schemas.emotion import EmotionAnalysisResult
from app.crud.user import get_user_by_id
from app.crud.chat_log import (
    create_chat_log, get_user_chat_history, get_chat_session_history,
    create_chat_session, end_chat_session, get_active_chat_session, get_user_sessions
)
from app.crud.emotion import create_emotion_record, get_user_recent_emotions
from app.crud.interest import get_user_interests
from app.services import (
    create_embedding, add_vector, search_similar_vectors, get_recent_context,
    analyze_text_emotion, analyze_user_profile
)
from app.services.gemini import generate_chat_response
from app.models.chat_log import ChatLog, ChatSession

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])

@router.post("/", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    사용자와의 대화 처리 - 완전한 RAG 시스템
    """
    try:
        # 1. 사용자 존재 확인
        user = await get_user_by_id(db, request.user_id)
        if not user:
            raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")
        
        # 2. 활성 채팅 세션 확인 또는 생성
        active_session = await get_active_chat_session(db, request.user_id)
        if not active_session:
            session_id = request.session_id or str(uuid.uuid4())
            session_data = ChatSessionCreate(
                user_id=request.user_id,
                session_id=session_id
            )
            active_session = await create_chat_session(db, session_data)
        
        # 3. 사용자 메시지 임베딩 생성
        try:
            user_embedding = await create_embedding(request.message, request.user_id)
            
            # 4. 사용자 메시지를 Qdrant에 저장
            user_vector_payload = ChatVectorPayload(
                user_id=request.user_id,
                session_id=active_session.session_id,
                message=request.message,
                role="user",
                timestamp=datetime.now()
            )
            user_vector_id = await add_vector(user_embedding, user_vector_payload)
            
            # 5. 유사한 과거 대화 검색
            similar_conversations = await search_similar_vectors(
                query_vector=user_embedding,
                user_id=request.user_id,
                limit=5,
                score_threshold=0.7
            )
            
            # 6. 최근 대화 컨텍스트 조회
            recent_context = await get_recent_context(request.user_id, hours_back=24)
            
        except Exception as e:
            logger.warning(f"RAG 검색 실패, 기본 모드로 전환: {str(e)}")
            similar_conversations = []
            recent_context = []
            user_vector_id = None
        
        # 7. 감정 분석
        try:
            emotion_result = await analyze_text_emotion(request.message, request.user_id)
        except Exception as e:
            logger.warning(f"감정 분석 실패: {str(e)}")
            emotion_result = None
        
        # 8. 사용자 정보 구성
        user_info = {
            "user_id": user.id,
            "name": user.name,
            "age": user.age,
            "gender": user.gender,
            "session_id": active_session.session_id
        }
        
        # 9. 대화 컨텍스트 구성
        try:
            chat_context = await build_chat_context(
                user_id=request.user_id,
                similar_conversations=similar_conversations,
                recent_context=recent_context,
                emotion_result=emotion_result,
                db=db
            )
        except Exception as e:
            logger.warning(f"컨텍스트 구성 실패: {str(e)}")
            chat_context = ChatPromptContext(
                user_info=user_info,
                conversation_history=[],
                similar_conversations=[],
                user_interests=[],
                recent_emotions=[],
                current_time=datetime.now(),
                system_instructions="고령층 사용자를 위한 친근하고 이해하기 쉬운 대화를 제공하세요."
            )
        
        # 10. Gemini 응답 생성
        try:
            gpt_response = await generate_chat_response(
                user_message=request.message,
                user_info=user_info,
                context=chat_context,
                conversation_history=recent_context
            )
            ai_response = gpt_response.response
            model_used = gpt_response.model_used
        except Exception as e:
            logger.warning(f"Gemini 응답 생성 실패: {str(e)}")
            ai_response = f"안녕하세요 {user.name}님! 무엇을 도와드릴까요?"
            model_used = "fallback"

        # 10-1. DB에 사용자 메시지 저장
        from app.schemas.chat import ChatLogCreate, RoleEnum, MessageTypeEnum
        await create_chat_log(db, ChatLogCreate(
            user_id=request.user_id,
            session_id=active_session.session_id,
            message=request.message,
            role=RoleEnum.USER,
            emotion=emotion_result.primary_emotion.value if emotion_result else None,
            emotion_score=emotion_result.intensity if emotion_result else None,
            message_type=MessageTypeEnum.TEXT
        ))
        # 10-2. DB에 챗봇 응답 저장
        await create_chat_log(db, ChatLogCreate(
            user_id=request.user_id,
            session_id=active_session.session_id,
            message=ai_response,
            role=RoleEnum.BOT,
            emotion=emotion_result.primary_emotion.value if emotion_result else None,
            emotion_score=emotion_result.intensity if emotion_result else None,
            message_type=MessageTypeEnum.TEXT
        ))
        
        # 11. 응답 반환
        return ChatResponse(
            session_id=active_session.session_id,
            response=ai_response,
            created_at=datetime.now(),
            emotion=emotion_result.primary_emotion.value if emotion_result else None,
            emotion_score=emotion_result.intensity if emotion_result else None,
            context_used=[conv.get('message', '') for conv in similar_conversations],
            similar_conversations=[],
            suggested_actions=[],
            response_time_ms=200,
            model_used=model_used
        )
        
    except Exception as e:
        logger.error(f"채팅 처리 중 오류 발생: {str(e)}")
        raise HTTPException(status_code=500, detail=f"채팅 처리 중 오류가 발생했습니다: {str(e)}")

@router.get("/history/{user_id}", response_model=ChatHistoryResponse)
async def get_chat_history(
    user_id: str,
    session_id: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db)
):
    """
    사용자의 채팅 기록 조회
    """
    try:
        # 사용자 존재 확인
        user = await get_user_by_id(db, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")
        # 채팅 기록 조회
        if session_id:
            chat_logs = await get_chat_session_history(db, user_id, session_id, limit, offset)
        else:
            chat_logs = await get_user_chat_history(db, user_id, limit, offset)
        # 전체 메시지 수
        from sqlalchemy import select, func
        total_count_result = await db.execute(select(func.count()).select_from(ChatLog).where(ChatLog.user_id == user_id))
        total_count = total_count_result.scalar() or 0
        # 세션 수
        session_count_result = await db.execute(select(func.count()).select_from(ChatSession).where(ChatSession.user_id == user_id))
        session_count = session_count_result.scalar() or 0
        # date_range 계산
        if chat_logs:
            oldest = min(log.created_at for log in chat_logs)
            newest = max(log.created_at for log in chat_logs)
            date_range = {"start": oldest, "end": newest}
        else:
            date_range = {"start": None, "end": None}
        # has_more 계산
        has_more = (offset + limit) < total_count
        # 메시지 변환
        from app.schemas.chat import ChatLogSchema
        messages = [ChatLogSchema.model_validate(log, from_attributes=True) for log in chat_logs]
        return ChatHistoryResponse(
            messages=messages,
            total_count=total_count,
            session_count=session_count,
            date_range=date_range,
            has_more=has_more
        )
    except Exception as e:
        logger.error(f"채팅 기록 조회 중 오류 발생: {str(e)}")
        raise HTTPException(status_code=500, detail=f"채팅 기록 조회 중 오류가 발생했습니다: {str(e)}")

@router.post("/session", response_model=ChatSessionResponse)
async def create_new_chat_session(
    request: ChatSessionRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    새로운 채팅 세션 생성
    """
    try:
        # 사용자 존재 확인
        user = await get_user_by_id(db, request.user_id)
        if not user:
            raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")
        
        # 기존 활성 세션 종료
        active_session = await get_active_chat_session(db, request.user_id)
        if active_session:
            await end_chat_session(db, active_session.id)
        
        # 새 세션 생성
        session_id = request.session_id or str(uuid.uuid4())
        session_data = ChatSessionCreate(
            user_id=request.user_id,
            session_id=session_id
        )
        new_session = await create_chat_session(db, session_data)
        
        return ChatSessionResponse(
            session_id=new_session.session_id,
            user_id=new_session.user_id,
            status="active",
            message="새로운 채팅 세션이 생성되었습니다",
            created_at=new_session.start_time
        )
        
    except Exception as e:
        logger.error(f"채팅 세션 생성 중 오류 발생: {str(e)}")
        raise HTTPException(status_code=500, detail=f"채팅 세션 생성 중 오류가 발생했습니다: {str(e)}")

@router.put("/session/{session_id}/end")
async def end_chat_session_endpoint(
    session_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    채팅 세션 종료
    """
    try:
        success = await end_chat_session(db, session_id)
        if not success:
            raise HTTPException(status_code=404, detail="채팅 세션을 찾을 수 없습니다")
        
        return {"message": "채팅 세션이 종료되었습니다", "session_id": session_id}
        
    except Exception as e:
        logger.error(f"채팅 세션 종료 중 오류 발생: {str(e)}")
        raise HTTPException(status_code=500, detail=f"채팅 세션 종료 중 오류가 발생했습니다: {str(e)}")

@router.delete("/session/{session_id}")
async def delete_chat_session(
    session_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    채팅 세션 삭제
    """
    try:
        # session_id 컬럼으로 세션 찾기
        result = await db.execute(select(ChatSession).where(ChatSession.session_id == session_id))
        session = result.scalar_one_or_none()
        if not session:
            raise HTTPException(status_code=404, detail="채팅 세션을 찾을 수 없습니다")
        await db.delete(session)
        await db.commit()
        return {"message": "채팅 세션이 성공적으로 삭제되었습니다", "session_id": session_id}
    except Exception as e:
        logger.error(f"채팅 세션 삭제 중 오류 발생: {str(e)}")
        raise HTTPException(status_code=500, detail=f"채팅 세션 삭제 중 오류가 발생했습니다: {str(e)}")

@router.get("/context/{user_id}")
async def get_chat_context(
    user_id: str,
    query: str,
    limit: int = 5,
    db: AsyncSession = Depends(get_db)
):
    """
    특정 쿼리에 대한 채팅 컨텍스트 조회
    """
    try:
        # 사용자 존재 확인
        user = await get_user_by_id(db, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")
        
        # 쿼리 임베딩 생성
        query_embedding = await create_embedding(query, user_id)
        
        # 유사 대화 검색
        similar_conversations = await search_similar_vectors(
            query_vector=query_embedding,
            user_id=user_id,
            limit=limit,
            score_threshold=0.5
        )
        
        # 최근 컨텍스트 조회
        recent_context = await get_recent_context(user_id, hours_back=24)
        
        return {
            "query": query,
            "similar_conversations": similar_conversations,
            "recent_context": recent_context[:10],  # 최근 10개만
            "context_count": len(similar_conversations) + len(recent_context)
        }
        
    except Exception as e:
        logger.error(f"채팅 컨텍스트 조회 중 오류 발생: {str(e)}")
        raise HTTPException(status_code=500, detail=f"채팅 컨텍스트 조회 중 오류가 발생했습니다: {str(e)}")

@router.get("/sessions/{user_id}")
async def get_chat_sessions_endpoint(
    user_id: str,
    limit: int = 20,
    offset: int = 0,
    db: AsyncSession = Depends(get_db)
):
    """
    사용자의 채팅 세션 목록 조회
    """
    try:
        user = await get_user_by_id(db, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")
        sessions = await get_user_sessions(db, user_id, limit, offset)
        # dict 변환
        session_dicts = [s.to_dict() for s in sessions]
        return session_dicts
    except Exception as e:
        logger.error(f"채팅 세션 목록 조회 중 오류 발생: {str(e)}")
        raise HTTPException(status_code=500, detail=f"채팅 세션 목록 조회 중 오류가 발생했습니다: {str(e)}")

# 헬퍼 함수들

async def build_chat_context(
    user_id: str,
    similar_conversations: List[Dict[str, Any]],
    recent_context: List[Dict[str, Any]],
    emotion_result: EmotionAnalysisResult,
    db: AsyncSession
) -> ChatPromptContext:
    """
    채팅 컨텍스트 구성
    """
    try:
        # 사용자 정보 조회
        user = await get_user_by_id(db, user_id)
        user_interests = await get_user_interests(db, user_id) if user else []
        
        # 최근 감정 상태 조회
        recent_emotions = await get_user_recent_emotions(db, user_id, days_back=7)
        emotion_list = [emotion.emotion for emotion in recent_emotions]
        
        # 사용자 정보 구성
        user_info = {
            "user_id": user.id if user else user_id,
            "name": user.name if user else "사용자",
            "age": user.age if user else 65,
            "gender": user.gender if user else "unknown"
        }
        
        # 대화 기록 변환
        conversation_history = []
        for context in recent_context[:10]:  # 최근 10개만
            if isinstance(context, dict) and 'payload' in context:
                payload = context['payload']
                conversation_history.append({
                    "user_id": payload.get('user_id', user_id),
                    "message": payload.get('message', ''),
                    "role": payload.get('role', 'user'),
                    "created_at": payload.get('timestamp', datetime.now())
                })
            elif hasattr(context, 'message'):  # 모델 객체인 경우
                conversation_history.append({
                    "user_id": getattr(context, 'user_id', user_id),
                    "message": context.message,
                    "role": context.role,
                    "created_at": context.created_at if hasattr(context, 'created_at') else datetime.now()
                })
        
        # 유사 대화 변환
        similar_conversations_content = []
        for conv in similar_conversations:
            payload = conv.get('payload', {})
            similar_conversations_content.append({
                'vector_id': conv.get('vector_id', payload.get('vector_id', "")),
                'message': payload.get('message', ''),
                'role': payload.get('role', 'user'),
                'similarity_score': conv.get('score', 0),
                'timestamp': payload.get('timestamp', datetime.now())
            })
        
        return ChatPromptContext(
            user_info=user_info,
            conversation_history=conversation_history,
            similar_conversations=similar_conversations_content,
            user_interests=user_interests if user_interests else [],
            recent_emotions=emotion_list,
            current_time=datetime.now(),
            system_instructions="고령층 사용자를 위한 친근하고 이해하기 쉬운 대화를 제공하세요."
        )
        
    except Exception as e:
        logger.error(f"채팅 컨텍스트 구성 중 오류: {str(e)}")
        # 기본 컨텍스트 반환
        return ChatPromptContext(
            user_info={"user_id": user_id, "name": "사용자", "age": 65, "gender": "unknown"},
            conversation_history=[],
            similar_conversations=[],
            user_interests=[],
            recent_emotions=[],
            current_time=datetime.now(),
            system_instructions="고령층 사용자를 위한 친근하고 이해하기 쉬운 대화를 제공하세요."
        )

async def update_user_profile_background(
    user_id: str,
    message: str,
    emotion_result: EmotionAnalysisResult,
    db: AsyncSession
):
    """
    사용자 프로필 백그라운드 업데이트
    """
    try:
        # 최근 채팅 기록 조회
        recent_chats = await get_user_chat_history(db, user_id, limit=100)
        
        # 채팅 기록을 딕셔너리 형태로 변환
        chat_history = []
        for chat in recent_chats:
            chat_history.append({
                'message': chat.message,
                'role': chat.role,
                'timestamp': chat.created_at
            })
        
        # 감정 기록 조회
        recent_emotions = await get_user_recent_emotions(db, user_id, days_back=30)
        emotion_history = []
        for emotion in recent_emotions:
            emotion_history.append({
                'emotion': emotion.emotion,
                'intensity': emotion.intensity,
                'timestamp': emotion.detected_at
            })
        
        # 사용자 프로필 분석
        profile_analysis = await analyze_user_profile(
            user_id=user_id,
            chat_history=chat_history,
            emotion_history=emotion_history
        )
        
        logger.info(f"사용자 프로필 백그라운드 업데이트 완료 - 사용자: {user_id}")
        
    except Exception as e:
        logger.error(f"사용자 프로필 백그라운드 업데이트 실패: {str(e)}")

# 채팅 통계 및 분석 엔드포인트

@router.get("/stats/{user_id}")
async def get_chat_stats(
    user_id: str,
    days_back: int = 30,
    db: AsyncSession = Depends(get_db)
):
    """
    사용자의 채팅 통계 조회
    """
    try:
        # 사용자 존재 확인
        user = await get_user_by_id(db, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")
        
        # 채팅 기록 조회
        chat_logs = await get_user_chat_history(db, user_id, limit=1000)
        
        # 기간 필터링
        cutoff_date = datetime.now() - timedelta(days=days_back)
        recent_chats = [
            chat for chat in chat_logs 
            if chat.created_at >= cutoff_date
        ]
        
        # 통계 계산
        total_messages = len(recent_chats)
        user_messages = len([chat for chat in recent_chats if chat.role == 'user'])
        assistant_messages = len([chat for chat in recent_chats if chat.role == 'assistant'])
        
        # 일별 메시지 수
        daily_counts = {}
        for chat in recent_chats:
            date_key = chat.created_at.strftime('%Y-%m-%d')
            daily_counts[date_key] = daily_counts.get(date_key, 0) + 1
        
        # 평균 메시지 길이
        avg_message_length = sum(len(chat.message) for chat in recent_chats) / total_messages if total_messages > 0 else 0
        
        return {
            "user_id": user_id,
            "period_days": days_back,
            "total_messages": total_messages,
            "user_messages": user_messages,
            "assistant_messages": assistant_messages,
            "daily_message_counts": daily_counts,
            "avg_message_length": round(avg_message_length, 1),
            "most_active_day": max(daily_counts.keys(), key=lambda k: daily_counts[k]) if daily_counts else None
        }
        
    except Exception as e:
        logger.error(f"채팅 통계 조회 중 오류 발생: {str(e)}")
        raise HTTPException(status_code=500, detail=f"채팅 통계 조회 중 오류가 발생했습니다: {str(e)}") 