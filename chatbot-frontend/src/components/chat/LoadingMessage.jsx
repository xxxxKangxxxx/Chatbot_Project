import React from 'react';
import { Bot, Sparkles, Zap } from 'lucide-react';

function LoadingMessage() {
  return (
    <div className="message bot">
      <div className="loading-message-container">
        {/* Bot Avatar */}
        <div className="loading-avatar">
          <div className="loading-avatar-inner">
            <Bot className="loading-bot-icon" />
            <div className="loading-status-indicator">
              <div className="loading-status-dot"></div>
            </div>
          </div>
        </div>

        {/* Message Content */}
        <div className="loading-content">
          {/* Message Header */}
          <div className="loading-header">
            <div className="loading-title-section">
              <span className="loading-bot-name">실버케어 AI</span>
              <div className="loading-premium-badge">
                Premium
              </div>
            </div>
            <div className="loading-status-badge">
              <Zap className="loading-status-icon" />
              <span>답변 생성 중...</span>
            </div>
          </div>
          
          {/* Typing Indicator */}
          <div className="loading-bubble">
            <div className="loading-decorative">
              <Sparkles className="loading-sparkles" />
            </div>
            
            {/* Typing Animation */}
            <div className="loading-typing-section">
              <div className="loading-dots">
                <div className="loading-dot loading-dot-1"></div>
                <div className="loading-dot loading-dot-2"></div>
                <div className="loading-dot loading-dot-3"></div>
              </div>
              <span className="loading-text">AI가 답변을 준비하고 있습니다</span>
            </div>
            
            {/* Progress Bar */}
            <div className="loading-progress-container">
              <div className="loading-progress-bar"></div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default LoadingMessage; 