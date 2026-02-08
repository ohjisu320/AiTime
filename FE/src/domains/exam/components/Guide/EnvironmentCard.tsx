import React from 'react';
import { cn } from '@/lib/utils';

interface EnvironmentCardProps {
  emoji: string;
  title: string;
  description: string;
  bgColor: string;
}

const EnvironmentCard: React.FC<EnvironmentCardProps> = ({ emoji, title, description, bgColor }) => (
  <div className="flex-1 min-w-[200px] h-full bg-white rounded-2xl shadow-lg flex flex-col items-center justify-center p-4 transition-transform hover:scale-[1.02]">
    <div className={cn("w-14 h-14 rounded-full flex justify-center items-center text-3xl mb-3", bgColor)}>
      {emoji}
    </div>
    <h3 className="text-base font-bold text-gray-800 mb-1">{title}</h3>
    <p className="text-xs text-gray-600 text-center leading-relaxed">
      {description}
    </p>
  </div>
);

export default EnvironmentCard;