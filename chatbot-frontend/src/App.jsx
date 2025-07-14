import React, { useEffect, useState } from 'react';
import Layout from './components/layout/Layout';
import LoadingScreen from './components/common/LoadingScreen';
import UserRegistration from './pages/UserRegistration';
import useStore from './stores/chatStore';
import './index.css';

function App() {
  const [isLoading, setIsLoading] = useState(true);
  const [isRegistered, setIsRegistered] = useState(false);
  const [currentUser, setCurrentUser] = useState(null);
  const { initializeChat } = useStore();

  useEffect(() => {
    // 앱 시작 시 초기 설정
    const initializeApp = async () => {
      try {
        // 기존 사용자 정보 확인
        const savedUserId = localStorage.getItem('userId');
        const savedUserName = localStorage.getItem('userName');
        
        if (savedUserId && savedUserName) {
          setCurrentUser({
            id: savedUserId,
            name: savedUserName
          });
          setIsRegistered(true);
          await initializeChat();
        }
        
        // 저장된 글자 크기 설정 적용
        const savedSettings = localStorage.getItem('userSettings');
        if (savedSettings) {
          const parsedSettings = JSON.parse(savedSettings);
          if (parsedSettings.display && parsedSettings.display.fontSize) {
            document.documentElement.setAttribute('data-font-size', parsedSettings.display.fontSize);
          }
        }
        
        // 최소 로딩 시간 보장 (UX를 위해)
        await new Promise(resolve => setTimeout(resolve, 2000));
        
        setIsLoading(false);
      } catch (error) {
        console.error('앱 초기화 중 오류:', error);
        setIsLoading(false);
      }
    };

    initializeApp();
  }, [initializeChat]);

  const handleLoadingComplete = () => {
    setIsLoading(false);
  };

  const handleRegistrationComplete = (userData) => {
    setCurrentUser(userData);
    setIsRegistered(true);
    // 채팅 스토어에 사용자 정보 반영
    initializeChat();
  };

  if (isLoading) {
    return <LoadingScreen onComplete={handleLoadingComplete} />;
  }

  if (!isRegistered) {
    return <UserRegistration onRegistrationComplete={handleRegistrationComplete} />;
  }

  return <Layout currentUser={currentUser} />;
}

export default App;
