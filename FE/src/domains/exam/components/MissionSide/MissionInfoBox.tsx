import React from 'react';

const MissionInfoBox: React.FC = () => (
  <div className="bg-white rounded-3xl p-8 shadow-lg border border-gray-100">
    <h4 className="text-gray-800 text-lg font-bold mb-5 flex items-center gap-2">
      📌 검사 진행 안내
    </h4>
    <ul className="space-y-4">
      {[
        "한 번에 모든 검사를 완료하지 않아도 됩니다.",
        "촬영 중 문제가 발생하면 언제든 다시 촬영할 수 있습니다.",
        "4개 검사를 모두 완료하면 AI 분석을 시작할 수 있습니다."
      ].map((text, idx) => (
        <li key={idx} className="flex gap-3 text-sm text-gray-600 leading-snug">
          <span className="text-indigo-400 font-bold">•</span>
          {text}
        </li>
      ))}
    </ul>
  </div>
);

export default MissionInfoBox;