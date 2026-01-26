import React from 'react';
import { CheckCircle2, PlayCircle, Lock } from 'lucide-react';
import { cn } from '@/lib/utils';

interface MissionCardProps {
  type: string;
  title: string;
  description: string;
  status: 'PENDING' | 'UPLOADED';
  onClick: () => void;
}

const MissionCard: React.FC<MissionCardProps> = ({ title, description, status, onClick }) => {
  const isCompleted = status === 'UPLOADED';

  return (
    <div 
      onClick={!isCompleted ? onClick : undefined}
      className={cn(
        "relative w-full p-6 rounded-2xl border-2 transition-all flex justify-between items-center shadow-sm",
        isCompleted 
          ? "bg-green-50 border-green-200 cursor-default" 
          : "bg-white border-gray-100 hover:border-[#6366F1] hover:shadow-md cursor-pointer"
      )}
    >
      <div className="flex flex-col gap-1">
        <div className="flex items-center gap-2">
          <h3 className={cn("text-xl font-bold", isCompleted ? "text-green-700" : "text-gray-800")}>
            {title}
          </h3>
          {isCompleted && <span className="text-xs bg-green-200 text-green-700 px-2 py-0.5 rounded-full font-bold">완료</span>}
        </div>
        <p className="text-gray-500 text-sm">{description}</p>
      </div>

      <div className="flex items-center">
        {isCompleted ? (
          <CheckCircle2 className="w-10 h-10 text-green-500" />
        ) : (
          <PlayCircle className="w-10 h-10 text-[#6366F1] opacity-80 group-hover:opacity-100" />
        )}
      </div>
    </div>
  );
};

export default MissionCard;