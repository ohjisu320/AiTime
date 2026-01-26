import React from 'react';
import { cn } from '@/lib/utils';

interface CardIconProps {
  variant: 'pink' | 'purple' | 'blue' | 'emerald';
}

const CardIcon: React.FC<CardIconProps> = ({ variant }) => {
  const bgColors = {
    pink: 'bg-pink-400',
    purple: 'bg-purple-400',
    blue: 'bg-blue-400',
    emerald: 'bg-emerald-500',
  };

  return (
    <div className={cn("w-16 h-16 rounded-2xl flex justify-center items-center shadow-sm", bgColors[variant])}>
      {/* 피그마의 상세 아이콘 대신 범용적인 흰색 박스로 표현 (Lucide 아이콘 추가 가능) */}
      <div className="w-8 h-8 border-4 border-white/40 rounded-lg" />
    </div>
  );
};

export default CardIcon;