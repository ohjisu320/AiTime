import React from 'react';
import { Play } from 'lucide-react';
import { cn } from '@/lib/utils';
import CardIcon from '../MissionCard/CardIcon';
import CardBadge from '../MissionCard/CardBadge';

interface MissionCardProps {
  title: string;
  subTitle: string;
  description: string;
  status: 'PENDING' | 'UPLOADED';
  variant: 'pink' | 'purple' | 'blue' | 'emerald' | 'amber' | 'violet';
  onClick: () => void; // 부모로부터 전달받는 함수 
}

const MissionCard: React.FC<MissionCardProps> = ({ 
  title, 
  subTitle, 
  description, 
  status, 
  variant, 
  onClick 
}) => {
  const isCompleted = status === 'UPLOADED';

  return (
    <div 
      onClick={onClick} // 👈 이 줄이 빠져있으면 부모의 로그가 찍히지 않습니다! 
      className={cn(
        "relative w-full p-8 rounded-[32px] flex items-center justify-between transition-all duration-300 border-2 shadow-xl cursor-pointer group",
        isCompleted 
          ? "border-green-400 bg-green-50/50" 
          : "border-gray-50 bg-white hover:border-indigo-300 hover:shadow-indigo-100"
      )}
    >
      <div className="flex items-center gap-6">
        <CardIcon variant={variant} />
        <div className="flex flex-col gap-1">
          <div className="flex items-center gap-2">
            <h3 className="text-gray-800 text-2xl font-bold">{title}</h3>
            {isCompleted && (
              <span className="bg-green-500 text-white text-[10px] px-2 py-0.5 rounded-md font-bold">완료</span>
            )}
          </div>
          <span className="text-gray-400 text-xs font-semibold uppercase tracking-widest">{subTitle}</span>
          <p className="text-gray-600 text-sm mt-1 leading-relaxed break-keep">{description}</p>
        </div>
      </div>

      <div className="flex items-center">
        {isCompleted ? (
          <div className="w-12 h-12 bg-green-500 rounded-full flex justify-center items-center">
            <span className="text-white text-xl font-bold">✓</span>
          </div>
        ) : (
          <div className="w-12 h-12 rounded-full border-2 border-indigo-400 flex justify-center items-center text-indigo-400 group-hover:bg-indigo-400 group-hover:text-white transition-colors">
            <Play className="w-5 h-5 fill-current ml-1" />
          </div>
        )}
      </div>
    </div>
  );
};

export default MissionCard;