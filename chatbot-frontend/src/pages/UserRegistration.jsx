import React, { useState } from 'react';
import { User, Heart, Calendar, Phone, Sparkles } from 'lucide-react';
import api from '../services/api';

function UserRegistration({ onRegistrationComplete }) {
  const [formData, setFormData] = useState({
    name: '',
    age: '',
    gender: '',
    phone: '',
    interests: []
  });
  
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [currentStep, setCurrentStep] = useState(1);

  const interestOptions = [
    { id: 'reading', label: '독서', icon: '📚' },
    { id: 'music', label: '음악 감상', icon: '🎵' },
    { id: 'gardening', label: '원예', icon: '🌱' },
    { id: 'cooking', label: '요리', icon: '🍳' },
    { id: 'walking', label: '산책', icon: '🚶' },
    { id: 'tv', label: 'TV 시청', icon: '📺' },
    { id: 'exercise', label: '운동', icon: '💪' },
    { id: 'crafts', label: '수공예', icon: '🎨' },
    { id: 'photography', label: '사진', icon: '📸' },
    { id: 'chess', label: '바둑/장기', icon: '♟️' }
  ];

  const handleInputChange = (field, value) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
    setError('');
  };

  const handleInterestToggle = (interestId) => {
    setFormData(prev => ({
      ...prev,
      interests: prev.interests.includes(interestId)
        ? prev.interests.filter(id => id !== interestId)
        : [...prev.interests, interestId]
    }));
  };

  const validateStep = (step) => {
    switch (step) {
      case 1:
        if (!formData.name.trim()) {
          setError('이름을 입력해주세요.');
          return false;
        }
        if (!formData.age || formData.age < 1 || formData.age > 120) {
          setError('올바른 나이를 입력해주세요.');
          return false;
        }
        break;
      case 2:
        if (!formData.gender) {
          setError('성별을 선택해주세요.');
          return false;
        }
        break;
      case 3:
        // 관심사는 선택사항
        break;
      default:
        break;
    }
    return true;
  };

  const handleNext = () => {
    if (validateStep(currentStep)) {
      setCurrentStep(prev => prev + 1);
      setError('');
    }
  };

  const handlePrevious = () => {
    setCurrentStep(prev => prev - 1);
    setError('');
  };

  const handleSubmit = async () => {
    if (!validateStep(currentStep)) return;

    setIsLoading(true);
    setError('');

    try {
      const registrationData = {
        name: formData.name.trim(),
        age: parseInt(formData.age),
        gender: formData.gender,
        phone: formData.phone.trim() || null,
        interests: formData.interests
      };

      const response = await api.post('/users/register', registrationData);
      
      // 사용자 ID를 로컬 스토리지에 저장
      localStorage.setItem('userId', response.data.id);
      localStorage.setItem('userName', response.data.name);
      
      // 등록 완료 콜백 호출
      onRegistrationComplete(response.data);
      
    } catch (error) {
      console.error('사용자 등록 실패:', error);
      setError(error.response?.data?.detail || '등록 중 오류가 발생했습니다. 다시 시도해주세요.');
    } finally {
      setIsLoading(false);
    }
  };

  const renderStep1 = () => (
    <div className="registration-step">
      <div className="step-header">
        <User className="step-icon" size={48} />
        <h2>기본 정보를 입력해주세요</h2>
        <p>안전하고 개인화된 서비스를 위해 필요합니다</p>
      </div>
      
      <div className="form-group">
        <label htmlFor="name">이름</label>
        <input
          id="name"
          type="text"
          value={formData.name}
          onChange={(e) => handleInputChange('name', e.target.value)}
          placeholder="예: 김영희"
          className="form-input"
        />
      </div>
      
      <div className="form-group">
        <label htmlFor="age">나이</label>
        <input
          id="age"
          type="number"
          value={formData.age}
          onChange={(e) => handleInputChange('age', e.target.value)}
          placeholder="예: 70"
          min="1"
          max="120"
          className="form-input"
        />
      </div>
      
      <div className="form-group">
        <label htmlFor="phone">전화번호 (선택사항)</label>
        <input
          id="phone"
          type="tel"
          value={formData.phone}
          onChange={(e) => handleInputChange('phone', e.target.value)}
          placeholder="예: 010-1234-5678"
          className="form-input"
        />
      </div>
    </div>
  );

  const renderStep2 = () => (
    <div className="registration-step">
      <div className="step-header">
        <Heart className="step-icon" size={48} />
        <h2>성별을 선택해주세요</h2>
        <p>더 적절한 대화를 위해 필요합니다</p>
      </div>
      
      <div className="gender-options">
        <button
          type="button"
          className={`gender-option ${formData.gender === 'M' ? 'selected' : ''}`}
          onClick={() => handleInputChange('gender', 'M')}
        >
          <span className="gender-icon">👨</span>
          <span>남성</span>
        </button>
        <button
          type="button"
          className={`gender-option ${formData.gender === 'F' ? 'selected' : ''}`}
          onClick={() => handleInputChange('gender', 'F')}
        >
          <span className="gender-icon">👩</span>
          <span>여성</span>
        </button>
      </div>
    </div>
  );

  const renderStep3 = () => (
    <div className="registration-step">
      <div className="step-header">
        <Sparkles className="step-icon" size={48} />
        <h2>관심사를 선택해주세요</h2>
        <p>개인화된 대화를 위해 관심 있는 분야를 알려주세요 (선택사항)</p>
      </div>
      
      <div className="interests-grid">
        {interestOptions.map((interest) => (
          <button
            key={interest.id}
            type="button"
            className={`interest-option ${formData.interests.includes(interest.id) ? 'selected' : ''}`}
            onClick={() => handleInterestToggle(interest.id)}
          >
            <span className="interest-icon">{interest.icon}</span>
            <span className="interest-label">{interest.label}</span>
          </button>
        ))}
      </div>
      
      <div className="selected-count">
        선택된 관심사: {formData.interests.length}개
      </div>
    </div>
  );

  return (
    <div className="registration-container">
      <div className="registration-card">
        {/* 진행 표시기 */}
        <div className="progress-indicator">
          <div className="progress-bar">
            <div 
              className="progress-fill" 
              style={{ width: `${(currentStep / 3) * 100}%` }}
            />
          </div>
          <div className="step-numbers">
            {[1, 2, 3].map((step) => (
              <div 
                key={step}
                className={`step-number ${currentStep >= step ? 'active' : ''}`}
              >
                {step}
              </div>
            ))}
          </div>
        </div>

        {/* 단계별 콘텐츠 */}
        <div className="registration-content">
          {currentStep === 1 && renderStep1()}
          {currentStep === 2 && renderStep2()}
          {currentStep === 3 && renderStep3()}
        </div>

        {/* 오류 메시지 */}
        {error && (
          <div className="error-message">
            {error}
          </div>
        )}

        {/* 버튼 영역 */}
        <div className="registration-actions">
          {currentStep > 1 && (
            <button
              type="button"
              onClick={handlePrevious}
              className="btn btn-secondary"
              disabled={isLoading}
            >
              이전
            </button>
          )}
          
          {currentStep < 3 ? (
            <button
              type="button"
              onClick={handleNext}
              className="btn btn-primary"
              disabled={isLoading}
            >
              다음
            </button>
          ) : (
            <button
              type="button"
              onClick={handleSubmit}
              className="btn btn-primary"
              disabled={isLoading}
            >
              {isLoading ? '등록 중...' : '등록 완료'}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

export default UserRegistration; 