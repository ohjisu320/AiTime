// src/domains/exam/components/MissionCard/index.tsx
import React from 'react';
import { Play } from 'lucide-react';
import { cn } from '@/lib/utils';
import CardIcon from '@/components/common/CardIcon';
import CardBadge from '@/components/common/CardBadge';

interface MissionCardProps {
  title: string;
  subTitle?: string;
  description: string;
  status: 'PENDING' | 'UPLOADED';
  variant: 'pink' | 'purple' | 'blue' | 'emerald' | 'amber' | 'violet';
  onClick: () => void;
}

const MissionCard: React.FC<MissionCardProps> = ({
  title, subTitle, description, status, variant, onClick
}) => {
  const isCompleted = status === 'UPLOADED';

  return (
    <div
      onClick={onClick}
      className={cn(
        "relative w-full p-5 rounded-2xl flex items-center justify-between transition-all duration-300 border-2 shadow-lg cursor-pointer group",
        isCompleted
          ? "border-green-400 bg-green-50/50"
          : "border-gray-50 bg-white hover:border-indigo-300 hover:shadow-indigo-100"
      )}
    >
      <div className="flex items-center gap-4">
        {/* ✅ 개량된 CardIcon 사용 */}
        <CardIcon variant={variant} />

        <div className="flex flex-col gap-0.5">
          <div className="flex items-center gap-2">
            <h3 className="text-gray-800 text-lg font-bold">{title}</h3>
            {isCompleted && (
              <span className="bg-green-500 text-white text-[9px] px-1.5 py-0.5 rounded font-bold">완료</span>
            )}
          </div>
          <span className="text-gray-400 text-[10px] font-semibold uppercase tracking-wide">{subTitle}</span>
          <p className="text-gray-600 text-xs mt-0.5 leading-relaxed break-keep">{description}</p>
        </div>
      </div>

      <div className="flex items-center">
        {isCompleted ? (
          /* ✅ 개량된 CardBadge 사용 */
          <CardBadge />
        ) : (
          <div className="w-10 h-10 rounded-full border-2 border-indigo-400 flex justify-center items-center text-indigo-400 group-hover:bg-indigo-400 group-hover:text-white transition-colors">
            <Play className="w-4 h-4 fill-current ml-0.5" />
          </div>
        )}
      </div>
    </div>
  );
};

export default MissionCard;