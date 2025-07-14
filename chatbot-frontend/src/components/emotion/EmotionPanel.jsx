import React, { useState, useEffect } from 'react';
import { BsPersonWalking, BsMusicNoteBeamed, BsHeart, BsBook, BsTv, BsFlower1 } from 'react-icons/bs';
import { getEmotionStats, getDailyEmotionSummary, getRecentEmotions } from '../../services/api';

function EmotionPanel({ currentUser }) {
  const [emotionStats, setEmotionStats] = useState(null);
  const [dailySummary, setDailySummary] = useState(null);
  const [recentEmotions, setRecentEmotions] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  
  const userId = currentUser?.id || localStorage.getItem('userId');

  useEffect(() => {
    const fetchEmotionData = async () => {
      if (!userId) {
        setIsLoading(false);
        return;
      }

      try {
        setError(null);
        
        // 병렬로 모든 감정 데이터 가져오기
        const results = await Promise.allSettled([
          getEmotionStats(userId, 30),
          getDailyEmotionSummary(userId, 
            new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0], 
            new Date().toISOString().split('T')[0]
          ),
          getRecentEmotions(userId, 7)
        ]);

        // 각 결과 처리
        if (results[0].status === 'fulfilled') {
          setEmotionStats(results[0].value);
        } else {
          console.warn('감정 통계 로딩 실패:', results[0].reason);
        }

        if (results[1].status === 'fulfilled') {
          setDailySummary(results[1].value);
        } else {
          console.warn('일별 감정 요약 로딩 실패:', results[1].reason);
        }

        if (results[2].status === 'fulfilled') {
          setRecentEmotions(results[2].value.emotions || []);
        } else {
          console.warn('최근 감정 로딩 실패:', results[2].reason);
        }

      } catch (error) {
        console.error('감정 데이터 로딩 오류:', error);
        setError('감정 데이터를 불러오는 중 오류가 발생했습니다.');
      } finally {
        setIsLoading(false);
      }
    };

    fetchEmotionData();
  }, [userId]);

  const getEmotionLabel = (emotion) => {
    const emotionMap = {
      'happy': '행복',
      'sad': '슬픔',
      'angry': '화남',
      'fear': '두려움',
      'surprise': '놀람',
      'disgust': '혐오',
      'neutral': '평온',
      'joy': '기쁨',
      'lonely': '외로움',
      'excited': '흥분',
      'calm': '평온',
      'anxious': '불안',
      'content': '만족',
      'grateful': '감사',
      'hopeful': '희망적'
    };
    return emotionMap[emotion] || emotion;
  };

  const getEmotionColor = (emotion) => {
    const colorMap = {
      'happy': '#fbbf24',
      'joy': '#fbbf24',
      'excited': '#f59e0b',
      'grateful': '#10b981',
      'hopeful': '#06b6d4',
      'content': '#8b5cf6',
      'calm': '#3b82f6',
      'neutral': '#6b7280',
      'sad': '#64748b',
      'lonely': '#475569',
      'anxious': '#ef4444',
      'angry': '#dc2626',
      'fear': '#7c2d12',
      'disgust': '#991b1b',
      'surprise': '#f97316'
    };
    return colorMap[emotion] || '#6b7280';
  };

  const getEmotionKeywords = (emotionDistribution) => {
    return Object.keys(emotionDistribution || {})
      .sort((a, b) => emotionDistribution[b] - emotionDistribution[a])
      .slice(0, 6)
      .map(emotion => getEmotionLabel(emotion));
  };

  const getRecommendations = (dominantEmotion) => {
    const recommendationMap = {
      'sad': [
        { icon: BsPersonWalking, title: '산책하기', description: '가벼운 산책으로 기분을 전환해보세요', color: 'bg-green-50 text-green-600' },
        { icon: BsMusicNoteBeamed, title: '좋아하는 음악 듣기', description: '기분 좋은 음악으로 마음을 달래보세요', color: 'bg-purple-50 text-purple-600' }
      ],
      'lonely': [
        { icon: BsHeart, title: '가족과 통화하기', description: '가족이나 친구와 안부를 나눠보세요', color: 'bg-red-50 text-red-600' },
        { icon: BsTv, title: '재미있는 프로그램 시청', description: '좋아하는 TV 프로그램을 시청해보세요', color: 'bg-blue-50 text-blue-600' }
      ],
      'anxious': [
        { icon: BsBook, title: '독서하기', description: '좋아하는 책을 읽으며 마음을 진정시켜보세요', color: 'bg-orange-50 text-orange-600' },
        { icon: BsFlower1, title: '원예 활동', description: '식물을 돌보며 마음의 평화를 찾아보세요', color: 'bg-emerald-50 text-emerald-600' }
      ],
      'default': [
        { icon: BsPersonWalking, title: '산책하기', description: '주변 공원에서 30분 산책을 추천해요', color: 'bg-green-50 text-green-600' },
        { icon: BsMusicNoteBeamed, title: '추억의 음악', description: '1980년대 인기 가요를 들어보세요', color: 'bg-purple-50 text-purple-600' }
      ]
    };

    return recommendationMap[dominantEmotion] || recommendationMap['default'];
  };

  if (isLoading) {
    return (
      <div className="emotion-panel">
        <div className="loading-message">
          <p>감정 분석 데이터를 불러오는 중...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="emotion-panel">
        <div className="error-message">
          <p>{error}</p>
        </div>
      </div>
    );
  }

  // 데이터가 없는 경우
  if (!emotionStats || emotionStats.total_emotions === 0) {
    return (
      <div className="emotion-panel">
        <h2 className="emotion-title">감정 분석 결과</h2>
        <div className="no-emotion-data">
          <p>아직 감정 분석 데이터가 없습니다.</p>
          <p>채팅을 시작하시면 감정 분석 결과를 확인할 수 있어요! 😊</p>
        </div>
      </div>
    );
  }

  const emotionDistribution = emotionStats.emotion_distribution || {};
  const totalEmotions = emotionStats.total_emotions;
  const dominantEmotion = emotionStats.dominant_emotion;
  
  // 감정 분포를 백분율로 변환
  const emotionPercentages = Object.entries(emotionDistribution).map(([emotion, count]) => ({
    emotion,
    label: getEmotionLabel(emotion),
    percentage: Math.round((count / totalEmotions) * 100),
    color: getEmotionColor(emotion)
  })).sort((a, b) => b.percentage - a.percentage);

  // 주간 데이터 준비
  const weeklyData = dailySummary?.daily_summaries || [];
  const weekDays = ['월', '화', '수', '목', '금', '토', '일'];
  
  return (
    <div className="emotion-panel">
      <h2 className="emotion-title">감정 분석 결과</h2>
      
      {/* 오늘의 감정 상태 */}
      <div className="emotion-stats">
        <h3>최근 감정 상태</h3>
        
        {emotionPercentages.slice(0, 3).map((item, index) => (
          <div key={index} className="emotion-item">
            <div className="emotion-info">
              <span className="emotion-name">{item.label}</span>
              <span className="emotion-percentage">{item.percentage}%</span>
            </div>
            <div className="emotion-bar">
              <div 
                className="emotion-progress" 
                style={{
                  width: `${item.percentage}%`,
                  backgroundColor: item.color
                }}
              ></div>
            </div>
          </div>
        ))}
      </div>
      
      {/* 주간 감정 추이 */}
      {weeklyData.length > 0 && (
        <div className="weekly-chart">
          <h3>주간 감정 추이</h3>
          <div className="chart-container">
            {weeklyData.slice(-7).map((dayData, index) => {
              const height = Math.min(dayData.avg_intensity * 100, 100);
              const color = getEmotionColor(dayData.dominant_emotion);
              
              return (
                <div 
                  key={index}
                  className="chart-bar" 
                  style={{ 
                    height: `${height}%`,
                    backgroundColor: color
                  }}
                ></div>
              );
            })}
          </div>
          <div className="chart-labels">
            {weekDays.map((day, index) => (
              <span key={index}>{day}</span>
            ))}
          </div>
        </div>
      )}
      
      {/* 감정 키워드 */}
      <div className="emotion-keywords">
        <h3>감정 키워드</h3>
        <div className="keywords-container">
          {getEmotionKeywords(emotionDistribution).map((keyword, index) => (
            <span key={index} className="keyword-tag">
              {keyword}
            </span>
          ))}
        </div>
      </div>
      
      {/* 추천 활동 */}
      <div className="recommendations">
        <h3>추천 활동</h3>
        {getRecommendations(dominantEmotion).map((activity, index) => {
          const IconComponent = activity.icon;
          return (
            <div key={index} className={`recommendation ${activity.color}`}>
              <div className="recommendation-icon">
                <IconComponent />
              </div>
              <div className="recommendation-content">
                <h4>{activity.title}</h4>
                <p>{activity.description}</p>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

export default EmotionPanel; 