import React from 'react';
import { Bot } from 'lucide-react';
import LoadingMessage from './LoadingMessage';

function BotMessage({ message }) {
  const getEmotionClass = (emotion) => {
    switch (emotion) {
      case 'happy':
        return 'happy';
      case 'sad':
        return 'sad';
      case 'neutral':
        return 'neutral';
      default:
        return '';
    }
  };

  const getEmotionLabel = (emotion) => {
    switch (emotion) {
      case 'happy':
        return '행복 감지됨';
      case 'sad':
        return '슬픔 감지됨';
      case 'neutral':
        return '평온 감지됨';
      default:
        return null;
    }
  };

  if (message.isTyping) {
    return <LoadingMessage />;
  }

  return (
    <div className="message bot">
      <div className={`message-bubble bot ${getEmotionClass(message.emotion)}`}>
        <div className="message-header">
          <Bot size={20} />
          <span className="message-author">AI 챗봇</span>
          {message.emotion && (
            <span className="emotion-badge">
              {getEmotionLabel(message.emotion)}
            </span>
          )}
        </div>
        <p className="message-content">{message.content}</p>
        
        {message.quickReplies && (
          <div className="quick-replies">
            {message.quickReplies.map((reply, index) => (
              <button key={index} className="quick-reply">
                {reply}
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export default BotMessage; 