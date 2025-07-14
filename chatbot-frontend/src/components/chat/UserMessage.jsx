import React from 'react';

function UserMessage({ message }) {
  return (
    <div className="message user">
      <div className="message-bubble user">
        <p className="message-content">{message.content}</p>
      </div>
    </div>
  );
}

export default UserMessage; 