import React from 'react';
import { cn } from '@/lib/utils';

interface ReportButtonProps {
  isAllDone: boolean;
  onSend: () => void;
}

const ReportButton: React.FC<ReportButtonProps> = ({ isAllDone, onSend }) => (
  <button
    disabled={!isAllDone}
    onClick={onSend}
    className={cn(
      "w-full h-24 rounded-3xl text-3xl font-black transition-all shadow-2xl flex items-center justify-center",
      isAllDone 
        ? "bg-violet-500 text-white hover:bg-violet-600 active:scale-[0.98] shadow-violet-200" 
        : "bg-gray-200 text-gray-400 cursor-not-allowed"
    )}
  >
    리포트 전송하기
  </button>
);

export default ReportButton;