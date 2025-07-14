import React, { useState } from 'react';
import { BsChatDots, BsGraphUp, BsHeart, BsPerson } from 'react-icons/bs';

const navItems = [
  { id: 'chat', label: '채팅', icon: BsChatDots },
  { id: 'emotion', label: '분석', icon: BsGraphUp },
  { id: 'health', label: '건강', icon: BsHeart },
  { id: 'profile', label: '프로필', icon: BsPerson }
];

function MobileNavigation() {
  const [activeTab, setActiveTab] = useState('chat');

  return (
    <div className="mobile-nav">
      <div className="mobile-nav-container">
        {navItems.map((item) => {
          const IconComponent = item.icon;
          return (
            <div
              key={item.id}
              className={`mobile-nav-item ${activeTab === item.id ? 'active' : ''}`}
              onClick={() => setActiveTab(item.id)}
            >
              <div className="nav-icon">
                <IconComponent />
              </div>
              <span>{item.label}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}

export default MobileNavigation; 