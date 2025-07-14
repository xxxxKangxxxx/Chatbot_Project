import React from 'react';

function EmotionKeywords() {
  const keywords = ['행복', '활기', '평온', '추억', '감사', '희망'];

  return (
    <div className="flex flex-wrap gap-2">
      {keywords.map((keyword, index) => (
        <span
          key={index}
          className="bg-gradient-to-r from-indigo-50 to-purple-50 text-indigo-700 px-3 py-2 rounded-full text-sm font-medium border border-indigo-100 hover:from-indigo-100 hover:to-purple-100 transition-all duration-300"
        >
          #{keyword}
        </span>
      ))}
    </div>
  );
}

export default EmotionKeywords; 