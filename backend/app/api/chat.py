"""
채팅 API 라우터

사용자와의 대화를 처리하는 핵심 API입니다.
임베딩 생성 → Qdrant 저장/검색 → 감정 분석 → GPT 응답 생성 → 저장의 전체 플로우를 담당합니다.
"""

from typing import List, Dict, Any, Optional
import logging
import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.chat import (
    ChatRequest, ChatResponse, ChatHistoryResponse, ChatSessionRequest,
    ChatSessionResponse, ChatSessionCreate, ChatPromptContext, ChatVectorPayload
)
from app.schemas.emotion import EmotionAnalysisResult
from app.crud.user import get_user_by_id
from app.crud.chat_log import (
    create_chat_log, get_user_chat_history, get_chat_session_history,
    create_chat_session, end_chat_session, get_active_chat_session
)
from app.crud.emotion import create_emotion_record, get_user_recent_emotions
from app.services import (
    create_embedding, add_vector, search_similar_vectors, get_recent_context,
    analyze_text_emotion, analyze_user_profile
)
from app.services.gemini import generate_chat_response

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])

@router.post("/", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    사용자와의 대화 처리
    
    전체 플로우:
    1. 사용자 메시지 임베딩 생성
    2. Qdrant에 벡터 저장
    3. 유사한 과거 대화 검색
    4. 감정 분석
    5. 사용자 프로필 기반 컨텍스트 구성
    6. GPT 응답 생성
    7. 대화 및 감정 데이터 저장
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
        logger.info(f"사용자 메시지 임베딩 생성 시작 - 사용자: {request.user_id}")
        user_embedding = await create_embedding(request.message, request.user_id)
        
        # 4. 사용자 메시지를 Qdrant에 저장
        user_vector_payload = ChatVectorPayload(
            user_id=request.user_id,
            session_id=active_session.id,
            message=request.message,
            role="user",
            timestamp=datetime.now()
        )
        user_vector_id = await add_vector(user_embedding, user_vector_payload)
        
        # 5. 유사한 과거 대화 검색
        logger.info(f"유사 대화 검색 시작 - 사용자: {request.user_id}")
        similar_conversations = await search_similar_vectors(
            query_vector=user_embedding,
            user_id=request.user_id,
            limit=5,
            score_threshold=0.7
        )
        
        # 6. 최근 대화 컨텍스트 조회
        recent_context = await get_recent_context(request.user_id, hours_back=24)
        
        # 7. 감정 분석
        logger.info(f"감정 분석 시작 - 사용자: {request.user_id}")
        emotion_result = await analyze_text_emotion(request.message, request.user_id)
        
        # 8. 사용자 프로필 및 관심사 분석 (백그라운드)
        background_tasks.add_task(
            update_user_profile_background,
            request.user_id,
            request.message,
            emotion_result,
            db
        )
        
        # 9. 대화 컨텍스트 구성
        chat_context = await build_chat_context(
            user_id=request.user_id,
            similar_conversations=similar_conversations,
            recent_context=recent_context,
            emotion_result=emotion_result,
            db=db
        )
        
        # 10. 사용자 정보 조회
        user_info = {
            "user_id": user.id,
            "name": user.name,
            "age": user.age,
            "preferred_tone": user.preferred_tone,
            "personality_traits": user.personality_traits
        }
        
        # 11. Gemini 응답 생성
        logger.info(f"Gemini 응답 생성 시작 - 사용자: {request.user_id}")
        gpt_response = await generate_chat_response(
            user_message=request.message,
            user_info=user_info,
            context=chat_context,
            conversation_history=recent_context
        )
        
        # 12. Gemini 응답 임베딩 생성 및 저장
        response_embedding = await create_embedding(gpt_response.message, request.user_id)
        response_vector_payload = ChatVectorPayload(
            user_id=request.user_id,
            session_id=active_session.id,
            message=gpt_response.message,
            role="assistant",
            timestamp=gpt_response.timestamp,
            emotion=emotion_result.primary_emotion.value if emotion_result else None
        )
        response_vector_id = await add_vector(response_embedding, response_vector_payload)
        
        # 13. 대화 로그 저장
        user_chat_log = await create_chat_log(db, {
            "user_id": request.user_id,
            "session_id": active_session.id,
            "message": request.message,
            "role": "user",
            "vector_id": user_vector_id,
            "metadata": {
                "emotion": emotion_result.primary_emotion.value if emotion_result else None,
                "emotion_intensity": emotion_result.intensity if emotion_result else None
            }
        })
        
        assistant_chat_log = await create_chat_log(db, {
            "user_id": request.user_id,
            "session_id": active_session.id,
            "message": gpt_response.message,
            "role": "assistant",
            "vector_id": response_vector_id,
            "metadata": getattr(gpt_response, 'metadata', {})
        })
        
        # 14. 감정 데이터 저장
        if emotion_result:
            await create_emotion_record(db, {
                "user_id": request.user_id,
                "chat_log_id": user_chat_log.id,
                "emotion": emotion_result.primary_emotion.value,
                "intensity": emotion_result.intensity,
                "confidence": emotion_result.confidence,
                "detected_keywords": emotion_result.detected_keywords,
                "analysis_method": emotion_result.analysis_method
            })
        
        # 15. 응답 반환
        logger.info(f"채팅 처리 완료 - 사용자: {request.user_id}")
        
        return ChatResponse(
            message=gpt_response.message,
            role="assistant",
            timestamp=gpt_response.timestamp,
            emotion=emotion_result.primary_emotion if emotion_result else None,
            emotion_intensity=emotion_result.intensity if emotion_result else None,
            session_id=active_session.id,
            metadata={
                **getattr(gpt_response, 'metadata', {}),
                "user_vector_id": user_vector_id,
                "response_vector_id": response_vector_id,
                "similar_conversations_count": len(similar_conversations),
                "emotion_confidence": emotion_result.confidence if emotion_result else None
            }
        )
        
    except Exception as e:
        logger.error(f"채팅 처리 중 오류 발생: {str(e)}")
        raise HTTPException(status_code=500, detail=f"채팅 처리 중 오류가 발생했습니다: {str(e)}")

@router.get("/history/{user_id}", response_model=List[ChatHistoryResponse])
async def get_chat_history(
    user_id: str,
    session_id: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db)
):
    """
    사용자의 채팅 기록 조회
    
    Args:
        user_id: 사용자 ID
        session_id: 특정 세션 ID (선택사항)
        limit: 조회할 최대 개수
        offset: 조회 시작 위치
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
        
        # 응답 형식 변환
        history_responses = []
        for log in chat_logs:
            history_responses.append(ChatHistoryResponse(
                id=log.id,
                message=log.message,
                role=log.role,
                timestamp=log.timestamp,
                session_id=log.session_id,
                metadata={"emotion": log.emotion, "emotion_score": log.emotion_score}
            ))
        
        return history_responses
        
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
        user_interests = user.interests if user else []
        
        # 최근 감정 상태 조회
        recent_emotions = await get_user_recent_emotions(db, user_id, days_back=7)
        emotion_list = [emotion.emotion for emotion in recent_emotions]
        
        # 유사 대화 내용 추출
        similar_conversations_content = []
        for conv in similar_conversations:
            payload = conv.get('payload', {})
            similar_conversations_content.append({
                'content': payload.get('message', ''),
                'role': payload.get('role', 'user'),
                'timestamp': payload.get('timestamp'),
                'score': conv.get('score', 0)
            })
        
        return ChatPromptContext(
            user_interests=user_interests,
            recent_emotions=emotion_list,
            similar_conversations=similar_conversations_content,
            recent_context=recent_context,
            current_emotion=emotion_result.primary_emotion.value if emotion_result else None,
            emotion_intensity=emotion_result.intensity if emotion_result else None
        )
        
    except Exception as e:
        logger.error(f"채팅 컨텍스트 구성 중 오류: {str(e)}")
        # 기본 컨텍스트 반환
        return ChatPromptContext(
            user_interests=[],
            recent_emotions=[],
            similar_conversations=[],
            recent_context=[],
            current_emotion=None,
            emotion_intensity=None
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
            if chat.timestamp >= cutoff_date
        ]
        
        # 통계 계산
        total_messages = len(recent_chats)
        user_messages = len([chat for chat in recent_chats if chat.role == 'user'])
        assistant_messages = len([chat for chat in recent_chats if chat.role == 'assistant'])
        
        # 일별 메시지 수
        daily_counts = {}
        for chat in recent_chats:
            date_key = chat.timestamp.strftime('%Y-%m-%d')
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