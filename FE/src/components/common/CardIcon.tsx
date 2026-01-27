// src/components/common/CardIcon.tsx
import React from 'react';
import { cn } from '@/lib/utils';
import type { LucideIcon } from 'lucide-react';

interface CardIconProps {
  variant?: 'pink' | 'purple' | 'blue' | 'emerald' | 'amber' | 'violet';
  icon?: LucideIcon; // 원하는 아이콘 주입 가능 
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

const CardIcon: React.FC<CardIconProps> = ({ 
  variant = 'blue', 
  icon: Icon, 
  size = 'md',
  className 
}) => {
  const bgColors = {
    pink: 'bg-pink-500/10 text-pink-500',
    purple: 'bg-purple-500/10 text-purple-500',
    blue: 'bg-blue-500/10 text-blue-500',
    emerald: 'bg-emerald-500/10 text-emerald-500',
    amber: 'bg-amber-500/10 text-amber-500',
    violet: 'bg-violet-500/10 text-violet-500',
  };

  const sizes = {
    sm: 'w-12 h-12 rounded-xl',
    md: 'w-16 h-16 rounded-2xl',
    lg: 'w-20 h-20 rounded-[24px]',
  };

  return (
    <div className={cn(
      "flex justify-center items-center shadow-sm shrink-0", 
      bgColors[variant], 
      sizes[size],
      className
    )}>
      {Icon ? (
        <Icon size={size === 'sm' ? 20 : size === 'md' ? 32 : 40} className="opacity-80" />
      ) : (
        <div className={cn(
          "border-4 border-white/40 rounded-lg",
          size === 'sm' ? 'w-6 h-6' : size === 'md' ? 'w-8 h-8' : 'w-10 h-10'
        )} />
      )}
    </div>
  );
};

export default CardIcon;