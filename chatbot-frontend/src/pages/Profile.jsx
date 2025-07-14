import React, { useState, useEffect } from 'react';
import { BsPerson, BsCalendar, BsHeart, BsChat, BsGraphUp, BsGear, BsCamera, BsTelephone, BsEnvelope } from 'react-icons/bs';
import { getChatStats, getEmotionStats } from '../services/api';

function Profile({ currentUser }) {
  const [profileData, setProfileData] = useState({
    name: '',
    age: '',
    gender: '',
    phone: '',
    email: '',
    joinDate: '',
    interests: []
  });
  
  const [stats, setStats] = useState({
    totalMessages: 0,
    totalDays: 0,
    averageMessagesPerDay: 0,
    favoriteEmotions: [],
    healthScore: 85
  });
  
  const [isEditing, setIsEditing] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  const userId = currentUser?.id || localStorage.getItem('userId');

  useEffect(() => {
    const loadProfileData = async () => {
      try {
        // 로컬 스토리지에서 사용자 정보 불러오기
        const userName = localStorage.getItem('userName') || '사용자';
        const userAge = localStorage.getItem('userAge') || '';
        const userGender = localStorage.getItem('userGender') || '';
        const userPhone = localStorage.getItem('userPhone') || '';
        const userEmail = localStorage.getItem('userEmail') || '';
        const userInterests = JSON.parse(localStorage.getItem('userInterests') || '[]');
        
        setProfileData({
          name: userName,
          age: userAge,
          gender: userGender,
          phone: userPhone,
          email: userEmail,
          joinDate: '2024-01-15', // 임시 가입일
          interests: userInterests
        });

        // 통계 데이터 불러오기
        if (userId) {
          const [chatStats, emotionStats] = await Promise.allSettled([
            getChatStats(userId, 30),
            getEmotionStats(userId, 30)
          ]);

          let totalMessages = 0;
          let totalDays = 0;
          let favoriteEmotions = [];

          if (chatStats.status === 'fulfilled') {
            const chatData = chatStats.value;
            totalMessages = chatData.total_messages || 0;
            totalDays = Object.keys(chatData.daily_message_counts || {}).length;
          }

          if (emotionStats.status === 'fulfilled') {
            const emotionData = emotionStats.value;
            favoriteEmotions = emotionData.emotion_distribution || [];
          }

          setStats({
            totalMessages,
            totalDays,
            averageMessagesPerDay: totalDays > 0 ? Math.round(totalMessages / totalDays) : 0,
            favoriteEmotions: favoriteEmotions.slice(0, 3),
            healthScore: 85 + Math.floor(Math.random() * 15) // 임시 건강 점수
          });
        }
      } catch (error) {
        console.error('프로필 데이터 로딩 오류:', error);
      } finally {
        setIsLoading(false);
      }
    };

    loadProfileData();
  }, [userId]);

  const handleInputChange = (field, value) => {
    setProfileData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleSave = () => {
    // 로컬 스토리지에 저장
    localStorage.setItem('userName', profileData.name);
    localStorage.setItem('userAge', profileData.age);
    localStorage.setItem('userGender', profileData.gender);
    localStorage.setItem('userPhone', profileData.phone);
    localStorage.setItem('userEmail', profileData.email);
    localStorage.setItem('userInterests', JSON.stringify(profileData.interests));
    
    setIsEditing(false);
    alert('프로필이 성공적으로 저장되었습니다!');
  };

  const handleCancel = () => {
    // 원래 데이터로 복원
    const userName = localStorage.getItem('userName') || '사용자';
    const userAge = localStorage.getItem('userAge') || '';
    const userGender = localStorage.getItem('userGender') || '';
    const userPhone = localStorage.getItem('userPhone') || '';
    const userEmail = localStorage.getItem('userEmail') || '';
    const userInterests = JSON.parse(localStorage.getItem('userInterests') || '[]');
    
    setProfileData({
      ...profileData,
      name: userName,
      age: userAge,
      gender: userGender,
      phone: userPhone,
      email: userEmail,
      interests: userInterests
    });
    
    setIsEditing(false);
  };

  const getGenderLabel = (gender) => {
    switch (gender) {
      case 'male': return '남성';
      case 'female': return '여성';
      default: return '미설정';
    }
  };

  const getEmotionLabel = (emotion) => {
    const emotionMap = {
      happy: '행복',
      sad: '슬픔',
      angry: '화남',
      fear: '불안',
      neutral: '평온',
      surprise: '놀람'
    };
    return emotionMap[emotion] || emotion;
  };

  if (isLoading) {
    return (
      <div className="profile-page">
        <div className="loading-container">
          <div className="loading-spinner"></div>
          <p>프로필을 불러오는 중...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="profile-page">
      <div className="profile-header">
        <div className="profile-title">
          <BsPerson size={32} />
          <h1>마이페이지</h1>
        </div>
        <button 
          className="edit-profile-btn"
          onClick={() => setIsEditing(!isEditing)}
        >
          <BsGear size={16} />
          {isEditing ? '편집 취소' : '프로필 편집'}
        </button>
      </div>

      <div className="profile-content">
        {/* 프로필 정보 카드 */}
        <div className="profile-card">
          <div className="profile-avatar-section">
            <div className="profile-avatar-large">
              <BsPerson size={48} />
            </div>
            <button className="change-avatar-btn">
              <BsCamera size={16} />
              사진 변경
            </button>
          </div>
          
          <div className="profile-info-section">
            <div className="profile-info-grid">
              <div className="info-item">
                <label>이름</label>
                {isEditing ? (
                  <input
                    type="text"
                    value={profileData.name}
                    onChange={(e) => handleInputChange('name', e.target.value)}
                    className="profile-input"
                  />
                ) : (
                  <span className="info-value">{profileData.name}</span>
                )}
              </div>
              
              <div className="info-item">
                <label>나이</label>
                {isEditing ? (
                  <input
                    type="number"
                    value={profileData.age}
                    onChange={(e) => handleInputChange('age', e.target.value)}
                    className="profile-input"
                  />
                ) : (
                  <span className="info-value">{profileData.age}세</span>
                )}
              </div>
              
              <div className="info-item">
                <label>성별</label>
                {isEditing ? (
                  <select
                    value={profileData.gender}
                    onChange={(e) => handleInputChange('gender', e.target.value)}
                    className="profile-select"
                  >
                    <option value="">선택하세요</option>
                    <option value="male">남성</option>
                    <option value="female">여성</option>
                  </select>
                ) : (
                  <span className="info-value">{getGenderLabel(profileData.gender)}</span>
                )}
              </div>
              
              <div className="info-item">
                <label>전화번호</label>
                {isEditing ? (
                  <input
                    type="tel"
                    value={profileData.phone}
                    onChange={(e) => handleInputChange('phone', e.target.value)}
                    className="profile-input"
                  />
                ) : (
                  <span className="info-value">{profileData.phone || '미등록'}</span>
                )}
              </div>
              
              <div className="info-item">
                <label>이메일</label>
                {isEditing ? (
                  <input
                    type="email"
                    value={profileData.email}
                    onChange={(e) => handleInputChange('email', e.target.value)}
                    className="profile-input"
                  />
                ) : (
                  <span className="info-value">{profileData.email || '미등록'}</span>
                )}
              </div>
              
              <div className="info-item">
                <label>가입일</label>
                <span className="info-value">{profileData.joinDate}</span>
              </div>
            </div>
            
            {isEditing && (
              <div className="edit-actions">
                <button className="save-btn" onClick={handleSave}>
                  저장
                </button>
                <button className="cancel-btn" onClick={handleCancel}>
                  취소
                </button>
              </div>
            )}
          </div>
        </div>

        {/* 통계 카드들 */}
        <div className="stats-grid">
          <div className="stat-card">
            <div className="stat-icon">
              <BsChat size={24} />
            </div>
            <div className="stat-content">
              <h3>총 대화 수</h3>
              <p className="stat-number">{stats.totalMessages}</p>
              <small>지난 30일간</small>
            </div>
          </div>
          
          <div className="stat-card">
            <div className="stat-icon">
              <BsCalendar size={24} />
            </div>
            <div className="stat-content">
              <h3>활동 일수</h3>
              <p className="stat-number">{stats.totalDays}</p>
              <small>지난 30일간</small>
            </div>
          </div>
          
          <div className="stat-card">
            <div className="stat-icon">
              <BsGraphUp size={24} />
            </div>
            <div className="stat-content">
              <h3>일평균 대화</h3>
              <p className="stat-number">{stats.averageMessagesPerDay}</p>
              <small>메시지/일</small>
            </div>
          </div>
          
          <div className="stat-card">
            <div className="stat-icon">
              <BsHeart size={24} />
            </div>
            <div className="stat-content">
              <h3>건강 점수</h3>
              <p className="stat-number">{stats.healthScore}</p>
              <small>매우 좋음</small>
            </div>
          </div>
        </div>

        {/* 감정 분석 요약 */}
        {stats.favoriteEmotions.length > 0 && (
          <div className="emotion-summary-card">
            <h3>최근 감정 분석</h3>
            <div className="emotion-list">
              {stats.favoriteEmotions.map((emotion, index) => (
                <div key={index} className="emotion-item">
                  <span className="emotion-label">{getEmotionLabel(emotion.emotion)}</span>
                  <div className="emotion-bar">
                    <div 
                      className="emotion-progress"
                      style={{ width: `${emotion.percentage}%` }}
                    ></div>
                  </div>
                  <span className="emotion-percentage">{emotion.percentage.toFixed(1)}%</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* 빠른 연락처 */}
        <div className="quick-contact-card">
          <h3>빠른 연락처</h3>
          <div className="contact-actions">
            <button className="contact-btn">
              <BsTelephone size={20} />
              <span>가족에게 전화</span>
            </button>
            <button className="contact-btn">
              <BsEnvelope size={20} />
              <span>이메일 보내기</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Profile; 