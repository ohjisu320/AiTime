import React from 'react';
import { Loader2 } from 'lucide-react';
import { cn } from '@/lib/utils';

interface LoadingSpinnerProps {
  className?: string;
  size?: number;
  fullScreen?: boolean;
}

const LoadingSpinner = ({ 
  className, 
  size = 40, 
  fullScreen = false 
}: LoadingSpinnerProps) => {
  const spinnerContent = (
    <div className={cn("flex flex-col items-center justify-center gap-3", className)}>
      {/* Lucide의 Loader2 아이콘에 animate-spin을 적용해 회전시킵니다 */}
      <Loader2 
        className="animate-spin text-indigo-600" 
        size={size} 
      />
      <p className="text-gray-500 text-sm font-medium">데이터를 불러오는 중입니다...</p>
    </div>
  );

  if (fullScreen) {
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-white/80 backdrop-blur-sm">
        {spinnerContent}
      </div>
    );
  }

  return (
    <div className="w-full h-full flex items-center justify-center min-h-[200px]">
      {spinnerContent}
    </div>
  );
};

export default LoadingSpinner;