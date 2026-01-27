// src/components/common/BigActionButton.tsx (기존 ReportButton 통합)
import React from 'react';
import { cn } from '@/lib/utils';

interface BigActionButtonProps {
  children: React.ReactNode; // 버튼 텍스트 자유 변경 
  onClick: () => void;
  disabled?: boolean;
  variant?: 'violet' | 'indigo';
  className?: string;
}

const BigActionButton: React.FC<BigActionButtonProps> = ({ 
  children, 
  onClick, 
  disabled = false, 
  variant = 'violet',
  className
}) => {
  const variantStyles = {
    violet: "bg-violet-500 text-white hover:bg-violet-600 shadow-violet-200",
    indigo: "bg-indigo-600 text-white hover:bg-indigo-700 shadow-indigo-200",
  };

  return (
    <button
      disabled={disabled}
      onClick={onClick}
      className={cn(
        "w-full h-24 rounded-[32px] text-3xl font-black transition-all shadow-2xl flex items-center justify-center active:scale-[0.98]",
        disabled 
          ? "bg-gray-200 text-gray-400 cursor-not-allowed shadow-none" 
          : variantStyles[variant],
        className
      )}
    >
      {children}
    </button>
  );
};

export default BigActionButton;