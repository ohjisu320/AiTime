// src/domains/exam/components/Screening/ScriptCard.tsx
import React from 'react';
import { MessageCircle } from 'lucide-react';

interface ScriptCardProps {
  script: {
    lines: string[];
  };
}

const ScriptCard: React.FC<ScriptCardProps> = ({ script }) => (
  <div className="relative w-full bg-violet-50 rounded-2xl p-6 border border-violet-100">
    {/* 피그마의 좌상단 아이콘 디자인 */}
    <div className="absolute -left-3 -top-3 w-9 h-9 bg-white rounded-full shadow-md flex items-center justify-center border border-violet-200">
      <MessageCircle size={18} className="text-indigo-600" />
    </div>
    <div className="flex flex-col items-center gap-2 text-center">
      <p className="text-gray-800 text-xl font-bold leading-relaxed">{script.lines[0]}</p>
      <p className="text-indigo-600 text-2xl font-black leading-relaxed">{script.lines[1]}</p>
      <p className="text-gray-800 text-xl font-bold leading-relaxed">{script.lines[2]}</p>
    </div>
  </div>
);

export default ScriptCard;