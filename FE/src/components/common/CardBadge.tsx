// src/components/common/CardBadge.tsx
import React from 'react';
import { Check } from 'lucide-react';
import { cn } from '@/lib/utils';

interface CardBadgeProps {
  size?: 'sm' | 'md';
  className?: string;
}

const CardBadge: React.FC<CardBadgeProps> = ({ size = 'md', className }) => (
  <div className={cn(
    "flex items-center justify-center bg-green-500 rounded-full shadow-lg shadow-green-100",
    size === 'sm' ? "w-8 h-8" : "w-10 h-10",
    className
  )}>
    <Check className={cn("text-white stroke-[3px]", size === 'sm' ? "w-4 h-4" : "w-6 h-6")} />
  </div>
);

export default CardBadge;