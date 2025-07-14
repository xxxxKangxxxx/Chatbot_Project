import React from 'react';
import { Footprints, Music } from 'lucide-react';

function RecommendedActivities() {
  const activities = [
    {
      icon: Footprints,
      title: '산책하기',
      description: '주변 공원에서 30분 산책을 추천해요',
      color: 'bg-green-50 text-green-600'
    },
    {
      icon: Music,
      title: '추억의 음악',
      description: '1980년대 인기 가요를 들어보세요',
      color: 'bg-purple-50 text-purple-600'
    }
  ];

  return (
    <div className="mt-4">
      <h3 className="font-medium mb-2">추천 활동</h3>
      <div className="space-y-2">
        {activities.map((activity, index) => {
          const IconComponent = activity.icon;
          return (
            <div
              key={index}
              className={`flex items-start space-x-2 p-2 rounded-lg cursor-pointer hover:opacity-80 transition ${activity.color}`}
            >
              <IconComponent className="mt-1" size={16} />
              <div>
                <p className="font-medium text-sm">{activity.title}</p>
                <p className="text-xs text-gray-600">{activity.description}</p>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

export default RecommendedActivities; 