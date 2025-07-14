import { notificationService } from './notificationService';

const randomMessages = [
  "안녕하세요! 오늘 기분은 어떠신가요?",
  "새로운 취미를 시작해보는 건 어떨까요?",
  "오늘 날씨가 참 좋네요!",
  "최근에 재미있게 본 영화나 드라마가 있나요?",
  "운동하기 좋은 날씨인데, 산책 한번 어떠세요?",
  "오늘 하루는 어떻게 보내셨나요?",
  "새로운 음악을 추천해드릴까요?",
  "맛있는 음식을 먹으면 기분이 좋아질 거예요!",
  "힘내세요! 당신을 응원합니다.",
  "오늘도 좋은 하루 보내세요!"
];

class RandomChatService {
  constructor() {
    this.isActive = false;
    this.timeoutIds = [];
  }

  getRandomMessage() {
    const randomIndex = Math.floor(Math.random() * randomMessages.length);
    return randomMessages[randomIndex];
  }

  getRandomTime() {
    // 5분에서 30분 사이의 랜덤한 시간 (밀리초)
    return Math.floor(Math.random() * (25 * 60 * 1000)) + (5 * 60 * 1000);
  }

  start(onNewMessage) {
    this.isActive = true;
    this.scheduleNextMessage(onNewMessage);
  }

  scheduleNextMessage(onNewMessage) {
    if (!this.isActive) return;

    const delay = this.getRandomTime();
    const timeoutId = setTimeout(() => {
      const message = this.getRandomMessage();
      
      // 새 메시지 알림
      notificationService.showNotification('새로운 메시지가 도착했습니다!', {
        body: message,
        tag: 'random-chat',
        renotify: true
      });

      // 메시지 처리 콜백 실행
      if (onNewMessage) {
        onNewMessage({
          type: 'bot',
          content: message,
          timestamp: new Date().toISOString()
        });
      }

      // 다음 메시지 예약
      this.scheduleNextMessage(onNewMessage);
    }, delay);

    this.timeoutIds.push(timeoutId);
  }

  stop() {
    this.isActive = false;
    this.timeoutIds.forEach(id => clearTimeout(id));
    this.timeoutIds = [];
  }
}

export const randomChatService = new RandomChatService(); 