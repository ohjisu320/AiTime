// src/domains/exam/components/Screening/StatusCheckGroup.tsx
import React from 'react';
import { cn } from '@/lib/utils';
import { CheckCircle2, Video, Mic } from 'lucide-react';

interface StatusCheckGroupProps {
  isAligned: boolean;
  volume: number;
}

const StatusCheckGroup: React.FC<StatusCheckGroupProps> = ({ isAligned, volume }) => {
  const isQuiet = volume <= 30;

  return (
    <section className="space-y-4 animate-in fade-in slide-in-from-bottom-2 duration-500">
      <h3 className="text-gray-700 text-sm font-bold uppercase tracking-wider">시스템 체크</h3>
      <div className="grid grid-cols-2 gap-3">
        {/* 얼굴 위치 카드 */}
        <div className={cn(
          "p-4 rounded-2xl border flex flex-col items-center gap-2 transition-all duration-300",
          isAligned ? "bg-green-50 border-green-200 text-green-600" : "bg-gray-50 border-gray-100 text-gray-400"
        )}>
          {isAligned ? <CheckCircle2 size={20} className="scale-110" /> : <Video size={20} />}
          <span className="text-[11px] font-bold">얼굴 위치 {isAligned ? "완료" : "체크 중"}</span>
        </div>

        {/* 소음 적정 카드 */}
        <div className={cn(
          "p-4 rounded-2xl border flex flex-col items-center gap-2 transition-all duration-300",
          isQuiet ? "bg-green-50 border-green-200 text-green-600" : "bg-amber-50 border-amber-100 text-amber-500"
        )}>
          {isQuiet ? <CheckCircle2 size={20} className="scale-110" /> : <Mic size={20} />}
          <span className="text-[11px] font-bold">소음 {isQuiet ? "적정" : "높음"}</span>
        </div>
      </div>
    </section>
  );
};

export default StatusCheckGroup;