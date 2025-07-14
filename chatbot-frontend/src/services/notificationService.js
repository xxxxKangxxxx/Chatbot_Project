class NotificationService {
  constructor() {
    this.permission = null;
  }

  async requestPermission() {
    try {
      this.permission = await Notification.requestPermission();
      return this.permission === 'granted';
    } catch (error) {
      console.error('알림 권한 요청 중 오류 발생:', error);
      return false;
    }
  }

  async showNotification(title, options = {}) {
    if (!this.permission) {
      const granted = await this.requestPermission();
      if (!granted) return;
    }

    try {
      const notification = new Notification(title, {
        icon: '/bot-icon.png',
        badge: '/bot-icon.png',
        ...options
      });

      notification.onclick = () => {
        window.focus();
        notification.close();
      };
    } catch (error) {
      console.error('알림 표시 중 오류 발생:', error);
    }
  }
}

export const notificationService = new NotificationService(); 