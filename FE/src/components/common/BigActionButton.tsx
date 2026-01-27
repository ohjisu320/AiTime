import React from 'react';
import { cn } from '@/lib/utils';

interface BigActionButtonProps {
  children: React.ReactNode; // 버튼에 들어갈 텍스트나 아이콘 [cite: 2026-01-27]
  onClick: () => void;
  disabled?: boolean;
  variant?: 'violet' | 'indigo'; // 상황에 맞는 색상 선택 [cite: 2026-01-27]
  className?: string; // 추가적인 스타일(높이, 폰트 크기 등) 조정용 [cite: 2026-01-27]
}

const BigActionButton: React.FC<BigActionButtonProps> = ({ 
  children, 
  onClick, 
  disabled = false, 
  variant = 'violet',
  className
}) => {
  // 색상 테마 정의 [cite: 2026-01-27]
  const variantStyles = {
    violet: "bg-violet-500 text-white hover:bg-violet-600 shadow-violet-200",
    indigo: "bg-indigo-600 text-white hover:bg-indigo-700 shadow-indigo-200",
  };

  return (
    <button
      disabled={disabled}
      onClick={onClick}
      className={cn(
        // 공통 스타일: 큼직한 라운드, 그림자, 애니메이션 [cite: 2026-01-27]
        "w-full h-24 rounded-[32px] text-3xl font-black transition-all shadow-2xl flex items-center justify-center active:scale-[0.98]",
        disabled 
          ? "bg-gray-200 text-gray-400 cursor-not-allowed shadow-none" 
          : variantStyles[variant],
        className // 외부에서 주입한 스타일로 덮어쓰기 가능 [cite: 2026-01-27]
      )}
    >
      {children}
    </button>
  );
};

export default BigActionButton;