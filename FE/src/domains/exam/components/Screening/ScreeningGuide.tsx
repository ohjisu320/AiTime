// src/domains/exam/components/Screening/ScreeningGuide.tsx

import React from 'react';
import { cn } from '@/lib/utils';
import { Mic, Video, CheckCircle2, AlertCircle } from 'lucide-react'; // 아이콘 추가 
import MissionGuideHeader from './MissionGuideHeader';
import InstructionList from './InstructionList';
import ScriptCard from './ScriptCard';
import BigActionButton from '@/components/common/BigActionButton';
import StatusCheckGroup from './StatusCheckGroup'; 

interface ScreeningGuideProps {
  onStart: () => void;
  isReady: boolean;
  isAligned: boolean;
  volume: number;
  missionData: any;
  showSystemCheck?: boolean; // 👈 띄울지 말지 결정하는 옵션 (기본값 true) 
}

const ScreeningGuide: React.FC<ScreeningGuideProps> = ({ 
  onStart, isReady, isAligned, volume, missionData, showSystemCheck = true 
}) => {
  console.log("현재 미션:", missionData?.korTitle, "체크 표시 여부:", showSystemCheck);
  
  return (
    <div className="flex flex-col h-full bg-white">
      <MissionGuideHeader {...missionData} />

      <div className="flex-1 overflow-y-auto p-8 space-y-10 scrollbar-hide">
        <InstructionList title="이렇게 준비해주세요" items={missionData.instructions} />
        <ScriptCard script={missionData.script} />

        {/* ✅ showSystemCheck가 true일 때만 렌더링합니다  */}
        {showSystemCheck && (
          <>
            <hr className="border-gray-50" />
            <StatusCheckGroup isAligned={isAligned} volume={volume} />
          </>
        )}
      </div>

      <div className="p-8 bg-gray-50 border-t">
        <BigActionButton onClick={onStart} disabled={!isReady} variant="indigo">
          검사 시작하기
        </BigActionButton>
      </div>
    </div>
  );
};

export default ScreeningGuide;