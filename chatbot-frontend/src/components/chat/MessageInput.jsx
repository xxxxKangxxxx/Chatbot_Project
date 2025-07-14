import React, { useState } from 'react';
import { Smile, Mic, Send } from 'lucide-react';

function MessageInput({ onSendMessage, currentSessionId }) {
  const [input, setInput] = React.useState('');

  const handleSend = (e) => {
    if (e) e.preventDefault(); // form submit 시 새로고침 방지
    if (input.trim() !== '') {
      onSendMessage(input, currentSessionId);
      setInput('');
    }
  };

  return (
    <form className="message-input-container" onSubmit={handleSend}>
      <input
        type="text"
        value={input}
        onChange={(e) => setInput(e.target.value)}
        placeholder="메시지를 입력하세요..."
        className="message-input"
      />
      <button className="send-btn" type="submit">
        <span role="img" aria-label="send">➤</span>
      </button>
    </form>
  );
}

export default MessageInput; 