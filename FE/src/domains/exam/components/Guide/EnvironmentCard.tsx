import React from 'react';
import { cn } from '@/lib/utils';

interface EnvironmentCardProps {
  emoji: string;
  title: string;
  description: string;
  bgColor: string;
}

const EnvironmentCard: React.FC<EnvironmentCardProps> = ({ emoji, title, description, bgColor }) => (
  <div className="w-80 h-56 bg-white rounded-2xl shadow-lg flex flex-col items-center p-6 transition-transform hover:scale-[1.02]">
    <div className={cn("w-20 h-20 rounded-full flex justify-center items-center text-4xl mb-4", bgColor)}>
      {emoji}
    </div>
    <h3 className="text-lg font-bold text-gray-800 mb-2">{title}</h3>
    <p className="text-sm text-gray-600 text-center leading-relaxed">
      {description}
    </p>
  </div>
);

export default EnvironmentCard;