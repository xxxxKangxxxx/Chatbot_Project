import React from 'react';

function EmotionChart() {
  const emotions = [
    { name: '행복', value: 75, color: 'bg-yellow-400', bgColor: 'bg-yellow-100' },
    { name: '평온', value: 20, color: 'bg-blue-400', bgColor: 'bg-blue-100' },
    { name: '슬픔', value: 5, color: 'bg-gray-400', bgColor: 'bg-gray-100' }
  ];

  return (
    <div className="space-y-3">
      {emotions.map((emotion, index) => (
        <div key={index} className="space-y-2">
          <div className="flex justify-between items-center">
            <span className="text-sm font-medium text-gray-700">{emotion.name}</span>
            <span className="text-sm font-bold text-gray-800">{emotion.value}%</span>
          </div>
          <div className={`emotion-bar ${emotion.bgColor}`}>
            <div 
              className={`emotion-bar-fill ${emotion.color}`}
              style={{ width: `${emotion.value}%` }}
            />
          </div>
        </div>
      ))}
    </div>
  );
}

export default EmotionChart; 