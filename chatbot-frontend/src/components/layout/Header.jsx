import React, { useState, useRef, useEffect } from 'react';
import { BsPerson, BsGear, BsBell } from 'react-icons/bs';

function Header({ currentUser, onViewChange, currentView }) {
  const [showNotifications, setShowNotifications] = useState(false);
  const notificationRef = useRef(null);

  // 더미 알림 데이터 (실제로는 API에서 가져와야 함)
  const notifications = [
    {
      id: 1,
      title: '새로운 메시지',
      message: 'AI 챗봇이 감정 분석 결과를 업데이트했습니다.',
      time: '5분 전',
      type: 'message'
    },
    {
      id: 2,
      title: '일정 알림',
      message: '약 복용 시간이 다가오고 있습니다.',
      time: '30분 전',
      type: 'schedule'
    },
    {
      id: 3,
      title: '건강 팁',
      message: '오늘 하루 산책을 추천드립니다.',
      time: '2시간 전',
      type: 'health'
    }
  ];

  const handleTitleClick = () => {
    onViewChange('chat');
  };

  const handleSettingsClick = () => {
    onViewChange('settings');
  };

  const handleProfileClick = () => {
    onViewChange('profile');
  };

  const handleNotificationClick = () => {
    setShowNotifications(!showNotifications);
  };

  // 외부 클릭 시 드롭다운 닫기
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (notificationRef.current && !notificationRef.current.contains(event.target)) {
        setShowNotifications(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  return (
    <div className="header">
      <div className="header-container">
        <div className="header-left">
          <h1 
            className="header-title clickable" 
            onClick={handleTitleClick}
            style={{ cursor: 'pointer' }}
          >
            고령층 AI 챗봇 서비스
          </h1>
        </div>
        <div className="header-right">
          <div className="notification-container" ref={notificationRef}>
            <button 
              className="header-btn" 
              onClick={handleNotificationClick}
              title="알림"
            >
              <BsBell />
              {notifications.length > 0 && (
                <span className="notification-badge">{notifications.length}</span>
              )}
            </button>
            
            {showNotifications && (
              <div className="notification-dropdown">
                <div className="notification-header">
                  <h3>알림</h3>
                  <span className="notification-count">{notifications.length}개</span>
                </div>
                <div className="notification-list">
                  {notifications.length > 0 ? (
                    notifications.map((notification) => (
                      <div key={notification.id} className="notification-item">
                        <div className="notification-content">
                          <h4>{notification.title}</h4>
                          <p>{notification.message}</p>
                          <span className="notification-time">{notification.time}</span>
                        </div>
                      </div>
                    ))
                  ) : (
                    <div className="no-notifications">
                      <p>새로운 알림이 없습니다.</p>
                    </div>
                  )}
                </div>
                <div className="notification-footer">
                  <button className="view-all-btn">모든 알림 보기</button>
                </div>
              </div>
            )}
          </div>
          
          <button 
            className="header-btn" 
            onClick={handleSettingsClick}
            title="설정"
          >
            <BsGear />
          </button>
          <button 
            className="header-btn" 
            onClick={handleProfileClick}
            title="프로필"
          >
            <BsPerson />
          </button>
        </div>
      </div>
    </div>
  );
}

export default Header; 