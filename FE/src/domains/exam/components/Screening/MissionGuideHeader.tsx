// src/domains/exam/components/Screening/MissionGuideHeader.tsx
import React from 'react';

interface MissionGuideHeaderProps {
  step: string;
  engTitle: string;
  korTitle: string;
}

const MissionGuideHeader: React.FC<MissionGuideHeaderProps> = ({ step, engTitle, korTitle }) => (
  <div className="w-full h-28 px-8 pt-6 pb-2 bg-white border-b border-gray-100 flex flex-col justify-start items-start gap-2">
    <div className="flex justify-start items-center gap-2">
      <div className="px-3 py-1 bg-violet-50 rounded-full border border-violet-200">
        <span className="text-indigo-600 text-xs font-bold leading-none">Mission {step}</span>
      </div>
      <span className="text-gray-400 text-xs font-normal uppercase tracking-tight">{engTitle}</span>
    </div>
    <h2 className="text-gray-800 text-2xl font-bold tracking-tight">{korTitle}</h2>
  </div>
);

export default MissionGuideHeader;