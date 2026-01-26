import React from 'react';
import { Play } from 'lucide-react';
import { cn } from '@/lib/utils';
import CardIcon from './CardIcon';
import CardBadge from './CardBadge';

interface MissionCardProps {
  title: string;
  subTitle: string; // 👈 여기 추가된 것 확인!
  description: string;
  status: 'PENDING' | 'UPLOADED';
  variant: 'pink' | 'purple' | 'blue' | 'emerald';
  onClick: () => void;
}

const MissionCard: React.FC<MissionCardProps> = ({ 
  title, 
  subTitle, // 👈 여기서도 꼭 받아줘야 합니다!
  description, 
  status, 
  variant, 
  onClick 
}) => {
  const isCompleted = status === 'UPLOADED';

  return (
    <div className={cn(
      "relative aspect-square rounded-[32px] p-8 flex flex-col justify-between transition-all duration-300 border-2 shadow-xl overflow-hidden",
      isCompleted 
        ? "bg-green-50/50 border-green-200" 
        : "bg-white border-gray-50 hover:border-indigo-300 hover:-translate-y-1 hover:shadow-indigo-100"
    )}>
      {/* 상단 섹션 */}
      <div className="flex justify-between items-start">
        <CardIcon variant={variant} />
        {isCompleted && <CardBadge />}
      </div>

      {/* 텍스트 섹션 */}
      <div className="flex flex-col gap-1 mt-2">
        <h3 className="text-gray-800 text-2xl font-bold">{title}</h3>
        {/* 화면에 그리는 부분 추가 */}
        <span className="text-gray-400 text-xs font-semibold uppercase tracking-widest leading-4">
          {subTitle}
        </span>
        <p className="text-gray-600 text-sm mt-3 leading-relaxed break-keep">
          {description}
        </p>
      </div>

      {/* 액션 버튼 */}
      <button 
        onClick={!isCompleted ? onClick : undefined}
        className={cn(
          "h-11 px-6 rounded-2xl flex items-center justify-center gap-2 font-bold text-sm transition-all w-fit z-10",
          isCompleted 
            ? "bg-green-100 text-green-600 cursor-default" 
            : "bg-indigo-50 text-indigo-600 hover:bg-indigo-600 hover:text-white"
        )}
      >
        {isCompleted ? "검사 완료" : "시작하기"}
        {!isCompleted && <Play className="w-4 h-4 fill-current" />}
      </button>

      {/* 피그마 완료 효과 (원형 디자인) */}
      {isCompleted && (
        <div className="absolute -right-10 -top-10 w-40 h-40 bg-green-500/5 rounded-full" />
      )}
    </div>
  );
};

export default MissionCard;