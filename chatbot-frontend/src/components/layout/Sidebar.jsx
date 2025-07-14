import React, { useState, useEffect } from 'react';
import { BsPerson, BsHeart, BsMusicNoteBeamed, BsTelephone, BsCapsule, BsTv, BsTrash } from 'react-icons/bs';
import { getEmotionSummary, getChatSessions, createChatSession, deleteChatSession } from '../../services/api';

function Sidebar({ currentUser, onSessionSelect }) {
  const [emotionData, setEmotionData] = useState(null);
  const [sessions, setSessions] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [deletingId, setDeletingId] = useState(null);
  
  const userName = currentUser?.name || localStorage.getItem('userName') || '사용자';
  const userId = currentUser?.id || localStorage.getItem('userId');

  useEffect(() => {
    const fetchData = async () => {
      if (!userId) {
        setIsLoading(false);
        return;
      }
      try {
        // 감정 요약 데이터 가져오기
        const emotionSummary = await getEmotionSummary(userId);
        setEmotionData(emotionSummary);
        // 채팅 세션 목록 가져오기
        const sessionList = await getChatSessions(userId);
        setSessions(sessionList);
      } catch (error) {
        console.error('사이드바 데이터 로딩 오류:', error);
      } finally {
        setIsLoading(false);
      }
    };
    fetchData();
  }, [userId]);

  const handleNewChat = async () => {
    if (!userId) return;
    setCreating(true);
    try {
      const newSession = await createChatSession(userId);
      // 새 세션 생성 후 목록 갱신
      const sessionList = await getChatSessions(userId);
      setSessions(sessionList);
      if (onSessionSelect) onSessionSelect(newSession.session_id);
    } catch (error) {
      alert('새 채팅 생성에 실패했습니다.');
    } finally {
      setCreating(false);
    }
  };

  const handleDeleteSession = async (sessionId) => {
    if (!window.confirm('정말 이 채팅을 삭제하시겠습니까?')) return;
    setDeletingId(sessionId);
    try {
      await deleteChatSession(sessionId);
      const updatedSessions = sessions.filter(s => s.session_id !== sessionId);
      setSessions(updatedSessions);
      // 현재 선택된 세션이 삭제된 세션이면, 삭제한 세션을 제외한 세션들 중 start_time이 가장 최근인 세션으로 전환
      if (onSessionSelect && sessionId === window.currentSessionId) {
        if (updatedSessions.length > 0) {
          const sorted = [...updatedSessions].sort((a, b) => new Date(b.start_time) - new Date(a.start_time));
          onSessionSelect(sorted[0].session_id);
        } else {
          onSessionSelect(null);
        }
      }
    } catch (error) {
      alert('채팅 삭제에 실패했습니다.');
    } finally {
      setDeletingId(null);
    }
  };

  const formatTimeAgo = (dateString) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffInHours = Math.floor((now - date) / (1000 * 60 * 60));
    if (diffInHours < 1) return '방금 전';
    if (diffInHours < 24) return `${diffInHours}시간 전`;
    const diffInDays = Math.floor(diffInHours / 24);
    if (diffInDays < 7) return `${diffInDays}일 전`;
    return date.toLocaleDateString();
  };

  const formatKoreanDateTime = (dateString) => {
    const date = new Date(dateString);
    const year = date.getFullYear();
    const month = date.getMonth() + 1;
    const day = date.getDate();
    const hour = date.getHours();
    const minute = date.getMinutes().toString().padStart(2, '0');
    return `${year}년 ${month}월 ${day}일 ${hour}시${minute}분`;
  };

  return (
    <aside className="sidebar">
      {/* 사용자 프로필 */}
      <div className="sidebar-section">
        <div className="profile-info">
          <div className="profile-avatar">
            <BsPerson />
          </div>
          <div className="profile-details">
            <h3>{userName}</h3>
            <p>오늘도 좋은 하루 되세요!</p>
          </div>
          <div className="profile-status">
            <div className="status-item">
              <span className="status-icon"><BsHeart /></span>
              <span>기분 좋음</span>
            </div>
          </div>
        </div>
        {/* 새 채팅 버튼 */}
        <button className="new-chat-btn" onClick={handleNewChat} disabled={creating} style={{marginTop: 12, width: '100%'}}>
          {creating ? '생성 중...' : '+ 새 채팅'}
        </button>
      </div>

      {/* 감정 분석 */}
      {!isLoading && emotionData && emotionData.total_records > 0 && (
        <div className="sidebar-section">
          <h3 className="sidebar-title">감정 분석</h3>
          <div className="mood-indicator">
            <div className="mood-header">
              <span className="mood-label">오늘의 기분</span>
              <span className="mood-badge">
                {emotionData.dominant_emotion}
              </span>
            </div>
            <div className="mood-bar">
              <div 
                className="mood-progress" 
                style={{ 
                  width: `${Math.min(emotionData.avg_intensity * 100, 100)}%`,
                  backgroundColor: '#8b5cf6'
                }}
              ></div>
            </div>
            <div className="mood-details">
              <small>평균 강도: {(emotionData.avg_intensity * 100).toFixed(0)}%</small>
            </div>
          </div>
        </div>
      )}

      {/* 빠른 메뉴 */}
      <div className="sidebar-section">
        <h3 className="sidebar-title">빠른 메뉴</h3>
        <div className="quick-menu">
          <button className="quick-btn"><BsTelephone /> 가족에게 전화</button>
          <button className="quick-btn"><BsCapsule /> 약 복용 시간</button>
          <button className="quick-btn"><BsTv /> 오늘의 뉴스</button>
          <button className="quick-btn"><BsMusicNoteBeamed /> 취미 활동</button>
        </div>
      </div>

      {/* 최근 대화 (세션 기반) */}
      {!isLoading && sessions.length > 0 && (
        <div className="sidebar-section">
          <h3 className="sidebar-title">최근 대화</h3>
          <div className="recent-chats">
            {sessions.map((session) => (
              <div key={session.session_id} className="recent-chat-item" style={{display: 'flex', alignItems: 'center', justifyContent: 'space-between'}}>
                <div style={{flex: 1, cursor: 'pointer'}} onClick={() => onSessionSelect && onSessionSelect(session.session_id)}>
                  <span className="chat-time">{formatTimeAgo(session.start_time)}</span>
                  <p className="chat-preview">{
                    session.session_summary
                      ? session.session_summary.slice(0, 20)
                      : formatKoreanDateTime(session.start_time)
                  }</p>
                </div>
                <button
                  className="delete-chat-btn"
                  onClick={() => handleDeleteSession(session.session_id)}
                  disabled={deletingId === session.session_id}
                  style={{marginLeft: 8, background: 'none', border: 'none', cursor: 'pointer', color: '#888'}}
                  title="채팅 삭제"
                >
                  <BsTrash />
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 데이터 없음 안내 */}
      {!isLoading && (!emotionData || emotionData.total_records === 0) && sessions.length === 0 && (
        <div className="sidebar-section">
          <div className="no-data-message">
            <p>아직 대화 기록이 없습니다.</p>
            <p>채팅을 시작해보세요! 😊</p>
          </div>
        </div>
      )}
    </aside>
  );
}

export default Sidebar; 