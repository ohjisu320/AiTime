import React from 'react';
import { cn } from '@/lib/utils';

interface ConfirmModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
  title: React.ReactNode; // 줄바꿈을 위해 string 대신 ReactNode 사용
  confirmText?: string;
  cancelText?: string;
  confirmVariant?: 'violet' | 'indigo' | 'slate'; // 상황에 맞는 버튼 색상 선택
}

const ConfirmModal: React.FC<ConfirmModalProps> = ({
  isOpen,
  onClose,
  onConfirm,
  title,
  confirmText = '네',
  cancelText = '아니오',
  confirmVariant = 'violet'
}) => {
  if (!isOpen) return null;

  // 버튼 색상 매핑
  const variantStyles = {
    violet: 'bg-violet-400 hover:bg-violet-500',
    indigo: 'bg-indigo-600 hover:bg-indigo-700',
    slate: 'bg-slate-400 hover:bg-slate-500'
  };

  return (
    <div className="fixed inset-0 z-[150] flex items-center justify-center bg-black/40 backdrop-blur-sm">
      <div className="w-[512px] bg-white rounded-[32px] p-12 shadow-2xl flex flex-col items-center animate-in fade-in zoom-in duration-200">
        
        {/* ✅ 상단 성공 체크 아이콘 (피그마 공통 디자인) */}
        <div className="w-20 h-20 mb-8 border-4 border-green-600 rounded-2xl flex items-center justify-center">
          <div className="w-10 h-10 border-4 border-green-600 border-t-0 border-r-0 -rotate-45 mb-2" />
        </div>

        {/* ✅ 타이틀 영역 */}
        <h3 className="text-neutral-700 text-3xl font-bold text-center leading-tight mb-12 whitespace-pre-wrap">
          {title}
        </h3>

        {/* ✅ 하단 버튼 영역 */}
        <div className="flex gap-4 w-full justify-center">
          {/* 취소/아니오 버튼 (보통 회색으로 고정) */}
          <button
            onClick={onClose}
            className="w-28 h-12 bg-slate-300 hover:bg-slate-400 text-white rounded-xl font-bold transition-all active:scale-95"
          >
            {cancelText}
          </button>
          
          {/* 확정/네 버튼 (상황에 따라 색상 가변) */}
          <button
            onClick={onConfirm}
            className={cn(
              "w-28 h-12 text-white rounded-xl font-bold transition-all active:scale-95",
              variantStyles[confirmVariant]
            )}
          >
            {confirmText}
          </button>
        </div>
      </div>
    </div>
  );
};

export default ConfirmModal;