import React, { useEffect, useState } from 'react';
import { Bot, Sparkles, Heart, Zap } from 'lucide-react';

function LoadingScreen({ onComplete }) {
  const [progress, setProgress] = useState(0);
  const [currentMessage, setCurrentMessage] = useState(0);

  const messages = [
    "AI 챗봇을 초기화하고 있습니다...",
    "감정 분석 엔진을 준비하고 있습니다...",
    "사용자 맞춤 설정을 불러오고 있습니다...",
    "곧 시작됩니다..."
  ];

  useEffect(() => {
    const interval = setInterval(() => {
      setProgress(prev => {
        if (prev >= 100) {
          clearInterval(interval);
          setTimeout(onComplete, 500);
          return 100;
        }
        return prev + 2;
      });
    }, 40);

    return () => clearInterval(interval);
  }, [onComplete]);

  useEffect(() => {
    const messageInterval = setInterval(() => {
      setCurrentMessage(prev => (prev + 1) % messages.length);
    }, 800);

    return () => clearInterval(messageInterval);
  }, []);

  return (
    <div className="loading-screen">
      <div className="loading-container">
        {/* 로딩 애니메이션 */}
        <div className="loading-animation">
          <div className="logo-circle">
            <div className="logo-gradient"></div>
            <Bot className="bot-icon" size={60} />
            <Sparkles className="floating-icon sparkles" size={20} />
            <Heart className="floating-icon heart" size={16} />
            <Zap className="floating-icon zap" size={14} />
          </div>
          <div className="loading-waves">
            <div className="wave wave1"></div>
            <div className="wave wave2"></div>
            <div className="wave wave3"></div>
          </div>
        </div>

        {/* 제목 */}
        <h1 className="loading-title">고령층 AI 챗봇 서비스</h1>
        
        {/* 진행 메시지 */}
        <p className="loading-message">{messages[currentMessage]}</p>
        
        {/* 진행률 바 */}
        <div className="progress-container">
          <div className="progress-bar">
            <div 
              className="progress-fill" 
              style={{ width: `${progress}%` }}
            ></div>
          </div>
          <span className="progress-text">{progress}%</span>
        </div>

        {/* 로딩 점들 */}
        <div className="loading-dots">
          <div className="dot"></div>
          <div className="dot"></div>
          <div className="dot"></div>
        </div>
      </div>
    </div>
  );
}

export default LoadingScreen; 