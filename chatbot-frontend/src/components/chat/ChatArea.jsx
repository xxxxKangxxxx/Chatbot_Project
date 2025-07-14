import React, { useEffect } from 'react';
import ChatHeader from './ChatHeader';
import MessageList from './MessageList';
import MessageInput from './MessageInput';
import { notificationService } from '../../services/notificationService';
import useStore from '../../stores/chatStore';

const ChatArea = ({ currentSessionId }) => {
  const { messages, sendMessage, addMessage, loadChatHistory } = useStore();
  const setMessages = useStore((state) => state.setMessages);

  useEffect(() => {
    // 알림 권한 요청
    notificationService.requestPermission();
  }, []);

  useEffect(() => {
    // 세션이 바뀔 때마다 해당 세션의 메시지 불러오기
    if (currentSessionId) {
      loadChatHistory(currentSessionId);
    } else {
      setMessages([]); // 세션이 없으면 메시지 비우기
    }
  }, [currentSessionId, loadChatHistory, setMessages]);

  return (
    <div className="chat-area" style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <ChatHeader />
      <div style={{ flex: 1, overflowY: 'auto', padding: '20px' }}>
        <MessageList messages={messages} />
      </div>
      <div style={{ borderTop: '1px solid #eee', padding: '20px', backgroundColor: 'white' }}>
        <MessageInput onSendMessage={sendMessage} currentSessionId={currentSessionId} />
      </div>
    </div>
  );
};

export default ChatArea; 