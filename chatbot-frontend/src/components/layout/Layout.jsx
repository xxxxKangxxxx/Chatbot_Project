import React, { useState } from 'react';
import Header from './Header';
import Sidebar from './Sidebar';
import MobileNavigation from './MobileNavigation';
import ChatArea from '../chat/ChatArea';
import EmotionPanel from '../emotion/EmotionPanel';
import Settings from '../../pages/Settings';
import Profile from '../../pages/Profile';

function Layout({ currentUser }) {
  const [currentView, setCurrentView] = useState('chat');
  const [currentSessionId, setCurrentSessionId] = useState(null);

  const handleViewChange = (view) => {
    setCurrentView(view);
  };

  const renderMainContent = () => {
    switch (currentView) {
      case 'chat':
        return (
          <>
            {/* 사이드바 */}
            <Sidebar currentUser={currentUser} onSessionSelect={setCurrentSessionId} />

            {/* 채팅 영역 */}
            <div className="chat-area">
              <ChatArea currentUser={currentUser} currentSessionId={currentSessionId} />
            </div>

            {/* 감정 분석 패널 */}
            <aside className="emotion-panel">
              <EmotionPanel currentUser={currentUser} />
            </aside>
          </>
        );
      case 'settings':
        return <Settings currentUser={currentUser} />;
      case 'profile':
        return <Profile currentUser={currentUser} />;
      default:
        return (
          <>
            {/* 사이드바 */}
            <Sidebar currentUser={currentUser} onSessionSelect={setCurrentSessionId} />

            {/* 채팅 영역 */}
            <div className="chat-area">
              <ChatArea currentUser={currentUser} currentSessionId={currentSessionId} />
            </div>

            {/* 감정 분석 패널 */}
            <aside className="emotion-panel">
              <EmotionPanel currentUser={currentUser} />
            </aside>
          </>
        );
    }
  };

  return (
    <div className="layout">
      {/* 상단 헤더 */}
      <Header 
        currentUser={currentUser} 
        onViewChange={handleViewChange}
        currentView={currentView}
      />

      {/* 메인 콘텐츠 */}
      <main className="main-content">
        {renderMainContent()}
      </main>

      {/* 모바일 네비게이션 */}
      <MobileNavigation 
        currentView={currentView}
        onViewChange={handleViewChange}
      />
    </div>
  );
}

export default Layout; 