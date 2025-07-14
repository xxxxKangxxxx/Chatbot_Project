import React from 'react';
import { Bot, Phone, Video } from 'lucide-react';

function ChatHeader() {
  return (
    <div className="chat-header">
      <div className="chat-header-left">
        <div className="chat-avatar">
          <Bot size={24} />
        </div>
        <div className="chat-info">
          <h2>AI 챗봇</h2>
          <p className="chat-status">지금 대화 가능</p>
        </div>
      </div>
      <div className="chat-actions">
        <button className="chat-action-btn">
          <Phone size={18} />
        </button>
        <button className="chat-action-btn">
          <Video size={18} />
        </button>
      </div>
    </div>
  );
}

export default ChatHeader; 