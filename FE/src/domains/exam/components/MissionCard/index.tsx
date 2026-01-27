import React from 'react';
import { Play } from 'lucide-react';
import { cn } from '@/lib/utils';
import CardIcon from './CardIcon';
import CardBadge from './CardBadge';

interface MissionCardProps {
    title: string;
    subTitle: string;
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
          onClick={onClick} // 👈 이 이벤트 연결이 로그 실행의 핵심입니다. [cite: 2026-01-26]
          className={cn(
            "relative w-full p-8 rounded-[32px] flex items-center justify-between cursor-pointer transition-all border-2",
            isCompleted ? "border-green-400 bg-green-50/50" : "border-gray-50 bg-white"
          )}
        >
            {/* 왼쪽 콘텐츠 영역 */}
            <div className="flex items-center gap-6">
                <CardIcon variant={variant as any} />
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

            {/* 오른쪽 아이콘/상태 영역 */}
            <div className="flex items-center">
                {isCompleted ? (
                    <div className="w-12 h-12 bg-green-500 rounded-full flex justify-center items-center shadow-lg shadow-green-100">
                        <span className="text-white text-xl font-bold">✓</span>
                    </div>
                ) : (
                    <div className="w-12 h-12 rounded-full border-2 border-indigo-400 flex justify-center items-center text-indigo-400 group-hover:bg-indigo-400 group-hover:text-white transition-colors">
                        <Play className="w-5 h-5 fill-current ml-1" />
                    </div>
                )}
            </div>

            {/* 피그마 완료 효과 배경 */}
            {isCompleted && (
                <div className="absolute right-0 top-0 w-32 h-full bg-green-500/5 -z-10" />
            )}
        </div>
    );
};

export default MissionCard;