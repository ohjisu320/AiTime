import React from 'react';
import { Play } from 'lucide-react';

// TypeScript 에러(ts2322) 해결을 위한 정확한 Props 정의
interface HeroBannerProps {
  isEligible: boolean;    // 새 검사 가능 여부
  progress: number;       // 0 ~ 4 단계
  nextDate: string;       // 마감 기한 또는 다음 가능일
  hospitalCount: number;  // 연결된 병원 수
  onClick: () => void;    // 클릭 핸들러
}

const HeroBanner = ({ isEligible, progress, nextDate, hospitalCount, onClick }: HeroBannerProps) => {
  // 1. 상태 판별 로직 (이미지 시안 기준)
  const isFinished = progress === 4;
  const isInProgress = progress > 0 && progress < 4;
  const canStartNew = hospitalCount > 0 && isEligible && progress === 0;

  // 2. 텍스트 정보 결정
  const getTitle = () => {
    if (isFinished) return "최근 검사 영상 확인하기";
    if (isInProgress) return `진행률 ${progress}/4`;
    return "새 검사 시작하기";
  };

  const getDescription = () => {
    if (isFinished) return "리포트를 제출한 영상을 확인해보세요. 이미 제출한 영상은 삭제할 수 없습니다.";
    if (isInProgress) return `${nextDate}까지 검사를 마치지 않으면 해당 검사 기록은 초기화됩니다.`;
    return "아이의 성장 발달을 확인하고 전문적인 분석을 받아보세요.";
  };

  const getSubInfo = () => {
    if (isFinished || canStartNew) return "소요 시간: 약 15-20분 • 4가지 미션 포함";
    if (isInProgress) return `검사 시작일: ${new Date().toLocaleDateString()}`; // 실제 데이터가 있다면 연동 가능
    return `${nextDate}부터 검사가 가능합니다.`;
  };

  return (
    <section 
      onClick={onClick}
      className="relative w-full h-60 bg-gradient-to-r from-[#6366F1] to-[#4F46E5] rounded-3xl shadow-2xl overflow-hidden p-12 flex items-center gap-8 cursor-pointer transition-all hover:brightness-110 active:scale-[0.99]"
    >
      {/* 배경 장식 패턴 (이미지 시안 반영) */}
      <div className="absolute inset-0 opacity-10 pointer-events-none">
        <div className="absolute w-80 h-80 -right-20 -top-20 bg-white rounded-full blur-3xl" />
        <div className="absolute w-64 h-64 -left-20 top-20 bg-white rounded-full blur-3xl" />
      </div>

      {/* 재생 버튼 아이콘 영역 */}
      <div className="relative z-10 w-24 h-24 bg-white rounded-full flex items-center justify-center shrink-0 shadow-xl">
        <Play className="w-10 h-10 text-[#6366F1] fill-[#6366F1] ml-1" />
      </div>

      {/* 텍스트 컨텐츠 영역 */}
      <div className="relative z-10 flex flex-col gap-3 text-white">
        <div className="space-y-1">
          <h1 className="text-4xl font-bold tracking-tight">
            {getTitle()}
          </h1>
          <p className="text-white/90 text-xl font-medium">
            {getDescription()}
          </p>
        </div>
        
        {/* 하단 상세 정보 (소요 시간 등) */}
        <div className="flex items-center gap-2 text-white/70 text-sm font-medium">
          <span>{getSubInfo()}</span>
        </div>
      </div>
    </section>
  );
};

export default HeroBanner;