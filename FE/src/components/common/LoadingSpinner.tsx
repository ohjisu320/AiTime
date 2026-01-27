// src/components/common/LoadingSpinner.tsx 
import React from 'react';
import { cn } from '@/lib/utils'; // cn 유틸리티가 있다면 사용하세요

interface LoadingSpinnerProps {
  className?: string; // 👈 className을 받을 수 있도록 타입을 추가합니다. 
}

const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({ className }) => {
  return (
    <div className={cn("animate-spin rounded-full border-4 border-t-transparent border-indigo-500", className)}>
      {/* 스피너 아이콘 또는 스타일 정의 */}
    </div>
  );
};

export default LoadingSpinner;