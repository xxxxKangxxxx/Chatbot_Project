import { create } from 'zustand';

const useStore = create((set) => ({
  messages: [],
  isLoading: false,
  
  addMessage: (message) => set((state) => ({
    messages: [...state.messages, {
      ...message,
      id: `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
    }]
  })),

  setMessages: (messages) => set({ messages }),

  setLoading: (loading) => set({ isLoading: loading }),

  loadChatHistory: async (sessionId = null) => {
    set({ isLoading: true });
    try {
      const userId = localStorage.getItem('userId');
      if (!userId) {
        throw new Error('사용자 ID를 찾을 수 없습니다.');
      }
      let url = `http://localhost:8000/api/v1/chat/history/${userId}`;
      if (sessionId) {
        url += `?session_id=${sessionId}`;
      }
      const response = await fetch(url, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        }
      });
      if (!response.ok) {
        throw new Error(`채팅 기록을 불러오는데 실패했습니다: ${response.status}`);
      }
      const chatHistory = await response.json();
      const formattedMessages = (chatHistory.messages || []).map(msg => ({
        type: msg.role === 'user' ? 'user' : 'bot',
        content: msg.message,
        timestamp: msg.timestamp || msg.created_at,
        id: msg.id
      }));
      if (formattedMessages.length === 0) {
        formattedMessages.push({
          type: 'bot',
          content: '안녕하세요! 무엇을 도와드릴까요?',
          timestamp: new Date().toISOString(),
          id: `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
        });
      }
      set({ messages: formattedMessages });
    } catch (error) {
      console.error('채팅 기록을 불러오는 중 오류 발생:', error);
      set((state) => ({
        messages: [
          {
            type: 'bot',
            content: '안녕하세요! 무엇을 도와드릴까요?',
            timestamp: new Date().toISOString(),
            id: `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
          }
        ]
      }));
    } finally {
      set({ isLoading: false });
    }
  },

  initializeChat: async () => {
    set({ isLoading: true });
    try {
      await useStore.getState().loadChatHistory();
    } catch (error) {
      console.error('채팅 초기화 중 오류 발생:', error);
    } finally {
      set({ isLoading: false });
    }
  },

  sendMessage: async (content, sessionId = null) => {
    set({ isLoading: true });
    try {
      const userId = localStorage.getItem('userId');
      if (!userId) {
        throw new Error('사용자 ID를 찾을 수 없습니다.');
      }
      const userMessageId = `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
      set((state) => ({
        messages: [...state.messages, {
          type: 'user',
          content,
          timestamp: new Date().toISOString(),
          id: userMessageId
        }]
      }));
      const typingMessageId = `typing-${Date.now()}`;
      set((state) => ({
        messages: [...state.messages, {
          type: 'bot',
          content: '작성 중...',
          timestamp: new Date().toISOString(),
          id: typingMessageId,
          isTyping: true
        }]
      }));
      let apiUrl = 'http://localhost:8000/api/v1/chat';
      const body = {
        message: content,
        user_id: userId
      };
      if (sessionId) {
        body.session_id = sessionId;
      }
      const response = await fetch(apiUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(body)
      });
      if (!response.ok) {
        throw new Error(`API 응답이 실패했습니다: ${response.status}`);
      }
      const data = await response.json();
      set((state) => ({
        messages: [
          ...state.messages.filter(msg => msg.id !== typingMessageId),
          {
            type: 'bot',
            content: data.response,
            timestamp: new Date().toISOString(),
            id: `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
          }
        ]
      }));
    } catch (error) {
      console.error('메시지 전송 중 오류 발생:', error);
      set((state) => ({
        messages: [
          ...state.messages.filter(msg => !msg.isTyping),
          {
            type: 'bot',
            content: '죄송합니다. 메시지 처리 중 오류가 발생했습니다.',
            timestamp: new Date().toISOString(),
            id: `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
          }
        ]
      }));
    } finally {
      set({ isLoading: false });
    }
  }
}));

export default useStore; 