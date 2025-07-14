// API 관련 상수
export const API_ENDPOINTS = {
  CHAT: '/chat',
  USERS: '/users',
  EMOTIONS: '/emotions',
  SCHEDULES: '/schedules',
  INTERESTS: '/interests'
};

// 메시지 타입
export const MESSAGE_TYPES = {
  USER: 'user',
  BOT: 'bot',
  SYSTEM: 'system'
};

// 감정 타입
export const EMOTION_TYPES = {
  HAPPY: 'happy',
  SAD: 'sad',
  NEUTRAL: 'neutral',
  ANGRY: 'angry',
  EXCITED: 'excited',
  WORRIED: 'worried'
};

// 추천 활동 타입
export const RECOMMENDATION_TYPES = {
  WALKING: 'walking',
  FOOD: 'food',
  MUSIC: 'music',
  EXERCISE: 'exercise',
  SOCIAL: 'social'
};

// 로컬 스토리지 키
export const STORAGE_KEYS = {
  AUTH_TOKEN: 'authToken',
  USER_ID: 'userId',
  CHAT_HISTORY: 'chatHistory',
  USER_PREFERENCES: 'userPreferences'
};

// 기본 설정
export const DEFAULT_SETTINGS = {
  CHAT_HISTORY_LIMIT: 50,
  MESSAGE_TIMEOUT: 10000,
  TYPING_DELAY: 1500,
  AUTO_SCROLL_DELAY: 100
};

// 색상 테마
export const COLORS = {
  PRIMARY: '#4f46e5',
  SECONDARY: '#f8f9fa',
  ACCENT: '#ff8c00',
  SUCCESS: '#10b981',
  WARNING: '#f59e0b',
  ERROR: '#ef4444',
  EMOTIONS: {
    HAPPY: '#fbbf24',
    SAD: '#3b82f6',
    NEUTRAL: '#6b7280',
    ANGRY: '#ef4444',
    EXCITED: '#f59e0b',
    WORRIED: '#8b5cf6'
  }
};

// 반응형 브레이크포인트
export const BREAKPOINTS = {
  SM: '640px',
  MD: '768px',
  LG: '1024px',
  XL: '1280px'
};

export default {
  API_ENDPOINTS,
  MESSAGE_TYPES,
  EMOTION_TYPES,
  RECOMMENDATION_TYPES,
  STORAGE_KEYS,
  DEFAULT_SETTINGS,
  COLORS,
  BREAKPOINTS
}; 