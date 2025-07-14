import axios from 'axios';

// API 기본 설정
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: `${API_BASE_URL}/api/v1`,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 요청 인터셉터
api.interceptors.request.use(
  (config) => {
    // 토큰이 있다면 헤더에 추가
    const token = localStorage.getItem('authToken');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// 응답 인터셉터
api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    if (error.response?.status === 401) {
      // 인증 오류 처리
      localStorage.removeItem('authToken');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export default api;

// 사용자 등록 API
export const registerUser = async (userData) => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/users/register`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(userData),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('사용자 등록 API 호출 오류:', error);
    throw error;
  }
};

// 사용자 조회 API
export const getUser = async (userId) => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/users/${userId}`);
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('사용자 조회 API 호출 오류:', error);
    throw error;
  }
};

// 감정 통계 API
export const getEmotionStats = async (userId, daysBack = 30) => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/emotions/${userId}/stats?days_back=${daysBack}`);
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('감정 통계 API 호출 오류:', error);
    throw error;
  }
};

// 감정 요약 API
export const getEmotionSummary = async (userId, date = null) => {
  try {
    const url = date 
      ? `${API_BASE_URL}/api/v1/emotions/${userId}/summary?date=${date}`
      : `${API_BASE_URL}/api/v1/emotions/${userId}/summary`;
    
    const response = await fetch(url);
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('감정 요약 API 호출 오류:', error);
    throw error;
  }
};

// 최근 감정 API
export const getRecentEmotions = async (userId, daysBack = 7) => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/emotions/${userId}/recent?days_back=${daysBack}`);
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('최근 감정 API 호출 오류:', error);
    throw error;
  }
};

// 일별 감정 요약 API
export const getDailyEmotionSummary = async (userId, startDate = null, endDate = null) => {
  try {
    let url = `${API_BASE_URL}/api/v1/emotions/${userId}/daily`;
    const params = new URLSearchParams();
    
    if (startDate) params.append('start_date', startDate);
    if (endDate) params.append('end_date', endDate);
    
    if (params.toString()) {
      url += `?${params.toString()}`;
    }
    
    const response = await fetch(url);
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('일별 감정 요약 API 호출 오류:', error);
    throw error;
  }
};

// 채팅 통계 API
export const getChatStats = async (userId, daysBack = 30) => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/chat/stats/${userId}?days_back=${daysBack}`);
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('채팅 통계 API 호출 오류:', error);
    throw error;
  }
}; 

// 채팅 세션 목록 조회
export const getChatSessions = async (userId) => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/chat/sessions/${userId}`);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error('채팅 세션 목록 조회 오류:', error);
    throw error;
  }
};

// 새 채팅 세션 생성
export const createChatSession = async (userId) => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/chat/session`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user_id: userId })
    });
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error('새 채팅 세션 생성 오류:', error);
    throw error;
  }
};

// 채팅 세션 삭제
export const deleteChatSession = async (sessionId) => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/chat/session/${sessionId}`, {
      method: 'DELETE',
    });
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error('채팅 세션 삭제 오류:', error);
    throw error;
  }
}; 