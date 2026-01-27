// src/domains/exam/components/Screening/ScreeningGuide.tsx
import React from 'react';
import { cn } from '@/lib/utils';
import MissionGuideHeader from './MissionGuideHeader';
import InstructionList from './InstructionList';
import ScriptCard from './ScriptCard';

interface ScreeningGuideProps {
  onStart: () => void;
  isReady: boolean;
}

const ScreeningGuide: React.FC<ScreeningGuideProps> = ({ onStart, isReady }) => {
  // 예시 데이터 (실제로는 props나 constants에서 가져올 수 있습니다) 
  const missionInstructions = [
    { id: 1, text: "보호자와 아이가", boldText: "정면" , suffix: "을 바라보게 해주세요" },
    { id: 2, text: "아이가 화면 속", boldText: "가이드" , suffix: "안에 들어오게 해주세요" },
  ];

  const missionScript = {
    lines: ["아이에게", "\"와! 저기 좀 봐!\"", "라고 말하며 관심을 끌어주세요"]
  };

  return (
    <div className="flex flex-col h-full bg-white">
      {/* 1. 헤더  */}
      <MissionGuideHeader step="01" engTitle="Eye Contact" korTitle="눈맞춤 유도하기" />

      <div className="flex-1 overflow-y-auto p-8 space-y-10">
        {/* 2. 미션 준비 리스트  */}
        <InstructionList title="검사 전 준비해주세요" items={missionInstructions} />

        {/* 3. 대사 가이드 카드  */}
        <div className="space-y-4">
          <h3 className="text-gray-700 text-lg font-bold">아이에게 이렇게 말해주세요</h3>
          <ScriptCard script={missionScript} />
        </div>
      </div>

      {/* 4. 하단 버튼 영역  */}
      <div className="p-8 bg-gray-50 border-t border-gray-100 space-y-4">
        <div className="text-center text-sm font-medium text-gray-500">
          {isReady ? "✅ 모든 준비가 완료되었습니다!" : "📷 얼굴 위치와 🔇 주변 소음을 체크하고 있습니다."}
        </div>
        <button 
          onClick={onStart}
          disabled={!isReady}
          className={cn(
            "w-full h-20 text-xl font-bold rounded-2xl transition-all active:scale-95",
            isReady ? "bg-indigo-600 text-white shadow-xl shadow-indigo-100" : "bg-gray-200 text-gray-400 cursor-not-allowed"
          )}
        >
          검사 시작 버튼
        </button>
      </div>
    </div>
  );
};

export default ScreeningGuide;