import React from 'react';
import { cn } from '@/lib/utils';
import { Send } from 'lucide-react';

interface MissionSideProps {
  completedCount: number;
  totalCount: number;
  onSend: () => void;
}

const MissionSide: React.FC<MissionSideProps> = ({ completedCount, totalCount, onSend }) => {
  const isAllDone = completedCount === totalCount;

  return (
    <div className="w-[380px] flex flex-col gap-6 sticky top-32">
      {/* 안내 박스 */}
      <div className="bg-white rounded-3xl p-8 shadow-lg border border-gray-50">
        <h4 className="text-gray-800 text-lg font-bold mb-5 flex items-center gap-2">
          📌 미션 진행 안내
        </h4>
        <ul className="space-y-4">
          {[
            "한 번에 모든 미션을 완료하지 않아도 됩니다.",
            "촬영 중 문제가 발생하면 언제든 다시 촬영할 수 있습니다.",
            "4개 미션을 모두 완료하면 AI 분석이 자동으로 시작됩니다."
          ].map((text, idx) => (
            <li key={idx} className="flex gap-3 text-sm text-gray-600 leading-snug">
              <span className="text-indigo-400 font-bold">•</span>
              {text}
            </li>
          ))}
        </ul>
      </div>

      {/* 리포트 전송 버튼 (디자인 개선) */}
      <button
        disabled={!isAllDone}
        onClick={onSend}
        className={cn(
          "w-full h-24 rounded-2xl text-2xl font-black transition-all flex flex-col items-center justify-center gap-1 shadow-2xl",
          isAllDone 
            ? "bg-gradient-to-br from-violet-500 to-indigo-600 text-white shadow-indigo-200 active:scale-95" 
            : "bg-gray-200 text-gray-400 cursor-not-allowed"
        )}
      >
        <span className="text-xs font-medium opacity-80 uppercase tracking-widest">
          {completedCount}/{totalCount} Completed
        </span>
        리포트 전송하기
      </button>
    </div>
  );
};

export default MissionSide;