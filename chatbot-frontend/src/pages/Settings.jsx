import React, { useState, useEffect } from 'react';
import { BsGear, BsBell, BsPalette, BsShield, BsQuestionCircle, BsToggleOn, BsToggleOff } from 'react-icons/bs';

function Settings({ currentUser }) {
  const [settings, setSettings] = useState({
    notifications: {
      chatNotifications: true,
      scheduleReminders: true,
      healthTips: true,
      emailNotifications: false
    },
    display: {
      fontSize: 'medium',
      theme: 'light',
      highContrast: false
    },
    privacy: {
      dataSharing: false,
      analytics: true,
      locationServices: false
    },
    accessibility: {
      screenReader: false,
      keyboardNavigation: true,
      reducedMotion: false
    }
  });

  const [activeSection, setActiveSection] = useState('notifications');

  useEffect(() => {
    // 설정 불러오기 (localStorage에서)
    const savedSettings = localStorage.getItem('userSettings');
    if (savedSettings) {
      const parsedSettings = JSON.parse(savedSettings);
      setSettings(parsedSettings);
      
      // 저장된 글자 크기 설정 적용
      if (parsedSettings.display && parsedSettings.display.fontSize) {
        applyFontSize(parsedSettings.display.fontSize);
      }
    }
  }, []);

  const handleSettingChange = (section, key, value) => {
    const newSettings = {
      ...settings,
      [section]: {
        ...settings[section],
        [key]: value
      }
    };
    setSettings(newSettings);
    localStorage.setItem('userSettings', JSON.stringify(newSettings));
    
    // 글자 크기 변경 시 즉시 적용
    if (section === 'display' && key === 'fontSize') {
      applyFontSize(value);
    }
  };

  const applyFontSize = (fontSize) => {
    const rootElement = document.documentElement;
    rootElement.setAttribute('data-font-size', fontSize);
  };

  const ToggleSwitch = ({ enabled, onChange }) => (
    <button
      onClick={() => onChange(!enabled)}
      className={`toggle-switch ${enabled ? 'enabled' : 'disabled'}`}
    >
      {enabled ? <BsToggleOn size={24} /> : <BsToggleOff size={24} />}
    </button>
  );

  const settingSections = [
    {
      id: 'notifications',
      title: '알림 설정',
      icon: BsBell,
      description: '각종 알림을 관리합니다'
    },
    {
      id: 'display',
      title: '화면 설정',
      icon: BsPalette,
      description: '화면 표시 방식을 조정합니다'
    },
    {
      id: 'privacy',
      title: '개인정보 보호',
      icon: BsShield,
      description: '개인정보 및 데이터 사용을 관리합니다'
    },
    {
      id: 'accessibility',
      title: '접근성',
      icon: BsQuestionCircle,
      description: '사용 편의성을 향상시킵니다'
    }
  ];

  const renderNotificationSettings = () => (
    <div className="settings-content">
      <h3>알림 설정</h3>
      <div className="settings-group">
        <div className="setting-item">
          <div className="setting-info">
            <h4>채팅 알림</h4>
            <p>새로운 메시지 알림을 받습니다</p>
          </div>
          <ToggleSwitch
            enabled={settings.notifications.chatNotifications}
            onChange={(value) => handleSettingChange('notifications', 'chatNotifications', value)}
          />
        </div>
        
        <div className="setting-item">
          <div className="setting-info">
            <h4>일정 알림</h4>
            <p>약 복용, 병원 방문 등 일정 알림을 받습니다</p>
          </div>
          <ToggleSwitch
            enabled={settings.notifications.scheduleReminders}
            onChange={(value) => handleSettingChange('notifications', 'scheduleReminders', value)}
          />
        </div>
        
        <div className="setting-item">
          <div className="setting-info">
            <h4>건강 팁</h4>
            <p>맞춤형 건강 정보와 팁을 받습니다</p>
          </div>
          <ToggleSwitch
            enabled={settings.notifications.healthTips}
            onChange={(value) => handleSettingChange('notifications', 'healthTips', value)}
          />
        </div>
        
        <div className="setting-item">
          <div className="setting-info">
            <h4>이메일 알림</h4>
            <p>중요한 알림을 이메일로 받습니다</p>
          </div>
          <ToggleSwitch
            enabled={settings.notifications.emailNotifications}
            onChange={(value) => handleSettingChange('notifications', 'emailNotifications', value)}
          />
        </div>
      </div>
    </div>
  );

  const renderDisplaySettings = () => (
    <div className="settings-content">
      <h3>화면 설정</h3>
      <div className="settings-group">
        <div className="setting-item">
          <div className="setting-info">
            <h4>글자 크기</h4>
            <p>화면에 표시되는 글자 크기를 조정합니다</p>
          </div>
          <select
            value={settings.display.fontSize}
            onChange={(e) => handleSettingChange('display', 'fontSize', e.target.value)}
            className="setting-select"
          >
            <option value="small">작게</option>
            <option value="medium">보통</option>
            <option value="large">크게</option>
            <option value="extra-large">매우 크게</option>
          </select>
        </div>
        
        <div className="setting-item">
          <div className="setting-info">
            <h4>테마</h4>
            <p>화면의 색상 테마를 선택합니다</p>
          </div>
          <select
            value={settings.display.theme}
            onChange={(e) => handleSettingChange('display', 'theme', e.target.value)}
            className="setting-select"
          >
            <option value="light">밝은 테마</option>
            <option value="dark">어두운 테마</option>
            <option value="auto">자동</option>
          </select>
        </div>
        
        <div className="setting-item">
          <div className="setting-info">
            <h4>고대비 모드</h4>
            <p>텍스트와 배경의 대비를 높여 가독성을 향상시킵니다</p>
          </div>
          <ToggleSwitch
            enabled={settings.display.highContrast}
            onChange={(value) => handleSettingChange('display', 'highContrast', value)}
          />
        </div>
      </div>
    </div>
  );

  const renderPrivacySettings = () => (
    <div className="settings-content">
      <h3>개인정보 보호</h3>
      <div className="settings-group">
        <div className="setting-item">
          <div className="setting-info">
            <h4>데이터 공유</h4>
            <p>서비스 개선을 위한 익명 데이터 공유에 동의합니다</p>
          </div>
          <ToggleSwitch
            enabled={settings.privacy.dataSharing}
            onChange={(value) => handleSettingChange('privacy', 'dataSharing', value)}
          />
        </div>
        
        <div className="setting-item">
          <div className="setting-info">
            <h4>사용 분석</h4>
            <p>앱 사용 패턴 분석을 통해 맞춤형 서비스를 제공합니다</p>
          </div>
          <ToggleSwitch
            enabled={settings.privacy.analytics}
            onChange={(value) => handleSettingChange('privacy', 'analytics', value)}
          />
        </div>
        
        <div className="setting-item">
          <div className="setting-info">
            <h4>위치 서비스</h4>
            <p>위치 기반 서비스 및 추천 기능을 사용합니다</p>
          </div>
          <ToggleSwitch
            enabled={settings.privacy.locationServices}
            onChange={(value) => handleSettingChange('privacy', 'locationServices', value)}
          />
        </div>
      </div>
    </div>
  );

  const renderAccessibilitySettings = () => (
    <div className="settings-content">
      <h3>접근성</h3>
      <div className="settings-group">
        <div className="setting-item">
          <div className="setting-info">
            <h4>화면 읽기 지원</h4>
            <p>화면 읽기 프로그램과의 호환성을 향상시킵니다</p>
          </div>
          <ToggleSwitch
            enabled={settings.accessibility.screenReader}
            onChange={(value) => handleSettingChange('accessibility', 'screenReader', value)}
          />
        </div>
        
        <div className="setting-item">
          <div className="setting-info">
            <h4>키보드 탐색</h4>
            <p>키보드만으로 앱을 사용할 수 있도록 합니다</p>
          </div>
          <ToggleSwitch
            enabled={settings.accessibility.keyboardNavigation}
            onChange={(value) => handleSettingChange('accessibility', 'keyboardNavigation', value)}
          />
        </div>
        
        <div className="setting-item">
          <div className="setting-info">
            <h4>움직임 줄이기</h4>
            <p>애니메이션과 전환 효과를 최소화합니다</p>
          </div>
          <ToggleSwitch
            enabled={settings.accessibility.reducedMotion}
            onChange={(value) => handleSettingChange('accessibility', 'reducedMotion', value)}
          />
        </div>
      </div>
    </div>
  );

  const renderContent = () => {
    switch (activeSection) {
      case 'notifications':
        return renderNotificationSettings();
      case 'display':
        return renderDisplaySettings();
      case 'privacy':
        return renderPrivacySettings();
      case 'accessibility':
        return renderAccessibilitySettings();
      default:
        return renderNotificationSettings();
    }
  };

  return (
    <div className="settings-page">
      <div className="settings-header">
        <div className="settings-title">
          <BsGear size={32} />
          <h1>설정</h1>
        </div>
        <p className="settings-subtitle">서비스를 개인화하고 편의성을 향상시키세요</p>
      </div>
      
      <div className="settings-layout">
        <div className="settings-sidebar">
          <nav className="settings-nav">
            {settingSections.map((section) => {
              const IconComponent = section.icon;
              return (
                <button
                  key={section.id}
                  className={`settings-nav-item ${activeSection === section.id ? 'active' : ''}`}
                  onClick={() => setActiveSection(section.id)}
                >
                  <div className="nav-item-icon">
                    <IconComponent size={20} />
                  </div>
                  <div className="nav-item-content">
                    <h3>{section.title}</h3>
                    <p>{section.description}</p>
                  </div>
                </button>
              );
            })}
          </nav>
        </div>
        
        <div className="settings-main">
          {renderContent()}
        </div>
      </div>
    </div>
  );
}

export default Settings; 