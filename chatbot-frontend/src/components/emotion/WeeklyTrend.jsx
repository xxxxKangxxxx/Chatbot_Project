import React from 'react';

function WeeklyTrend() {
  const weekData = [
    { day: '월', value: 60, height: '60%' },
    { day: '화', value: 70, height: '70%' },
    { day: '수', value: 85, height: '85%' },
    { day: '목', value: 80, height: '80%' },
    { day: '금', value: 40, height: '40%' },
    { day: '토', value: 30, height: '30%' },
    { day: '일', value: 75, height: '75%' }
  ];

  return (
    <div className="space-y-4">
      <div className="flex items-end justify-between h-32 space-x-2">
        {weekData.map((data, index) => (
          <div key={index} className="flex flex-col items-center flex-1">
            <div className="w-full bg-gray-100 rounded-t-lg relative overflow-hidden" style={{ height: '100px' }}>
              <div 
                className="w-full bg-gradient-to-t from-blue-400 to-blue-500 rounded-t-lg absolute bottom-0 transition-all duration-500"
                style={{ height: data.height }}
              />
            </div>
            <span className="text-xs text-gray-600 mt-2 font-medium">{data.day}</span>
          </div>
        ))}
      </div>
      
      <div className="text-center">
        <p className="text-sm text-gray-600">
          이번 주 평균 행복 지수: <span className="font-semibold text-blue-600">66점</span>
        </p>
      </div>
    </div>
  );
}

export default WeeklyTrend; 