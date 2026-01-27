// src/components/common/InfoNoticeBox.tsx (기존 MissionInfoBox 통합)
import React from 'react';
import { cn } from '@/lib/utils';

interface InfoNoticeBoxProps {
  title: string;
  items: string[]; // 유의사항 리스트를 배열로 받음 
  className?: string;
}

const InfoNoticeBox: React.FC<InfoNoticeBoxProps> = ({ title, items, className }) => (
  <div className={cn("bg-white rounded-[32px] p-8 shadow-lg border border-gray-100", className)}>
    <h4 className="text-gray-800 text-lg font-bold mb-5 flex items-center gap-2">
      📌 {title}
    </h4>
    <ul className="space-y-4">
      {items.map((text, idx) => (
        <li key={idx} className="flex gap-3 text-sm text-gray-600 leading-snug">
          <span className="text-indigo-400 font-bold">•</span>
          {text}
        </li>
      ))}
    </ul>
  </div>
);

export default InfoNoticeBox;