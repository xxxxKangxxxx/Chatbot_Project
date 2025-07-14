import api from './api';

export const chatService = {
  // 메시지 전송
  async sendMessage(data) {
    try {
      const response = await api.post('/chat/', data);
      return response.data;
    } catch (error) {
      console.error('메시지 전송 실패:', error);
      throw error;
    }
  },

  // 채팅 기록 조회
  async getChatHistory(userId, limit = 50) {
    try {
      const response = await api.get(`/chat/history/${userId}`, {
        params: { limit }
      });
      return response.data;
    } catch (error) {
      console.error('채팅 기록 조회 실패:', error);
      throw error;
    }
  },

  // 채팅 세션 생성
  async createChatSession(userId) {
    try {
      const response = await api.post('/chat/session', { user_id: userId });
      return response.data;
    } catch (error) {
      console.error('채팅 세션 생성 실패:', error);
      throw error;
    }
  },

  // 채팅 세션 종료
  async endChatSession(sessionId) {
    try {
      const response = await api.put(`/chat/session/${sessionId}/end`);
      return response.data;
    } catch (error) {
      console.error('채팅 세션 종료 실패:', error);
      throw error;
    }
  },

  // 채팅 통계 조회
  async getChatStats(userId, daysBack = 30) {
    try {
      const response = await api.get(`/chat/stats/${userId}`, {
        params: { days_back: daysBack }
      });
      return response.data;
    } catch (error) {
      console.error('채팅 통계 조회 실패:', error);
      throw error;
    }
  }
};

export default chatService; 