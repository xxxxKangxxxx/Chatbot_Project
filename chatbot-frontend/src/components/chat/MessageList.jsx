import React, { useEffect, useRef } from 'react';
import BotMessage from './BotMessage';
import UserMessage from './UserMessage';

function MessageList({ messages }) {
  const bottomRef = useRef(null);

  useEffect(() => {
    if (bottomRef.current) {
      bottomRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages]);

  return (
    <>
      {messages.map((message) => (
        <div key={message.id} className="fade-in">
          {message.type === 'user' ? (
            <UserMessage message={message} />
          ) : (
            <BotMessage message={message} />
          )}
        </div>
      ))}
      <div ref={bottomRef} />
    </>
  );
}

export default MessageList; 