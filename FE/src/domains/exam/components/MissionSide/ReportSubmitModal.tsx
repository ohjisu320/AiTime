import React from 'react';

interface ReportSubmitModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
}

const ReportSubmitModal: React.FC<ReportSubmitModalProps> = ({ isOpen, onClose, onConfirm }) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-[110] flex items-center justify-center bg-black/40 backdrop-blur-sm">
      <div className="w-[512px] bg-white rounded-2xl p-10 shadow-2xl flex flex-col items-center animate-in fade-in zoom-in duration-200">
        {/* 피그마의 녹색 체크 박스 디자인 */}
        <div className="w-20 h-24 mb-6 border-4 border-green-600 rounded-xl flex items-center justify-center">
          <div className="w-10 h-7 border-4 border-green-600 border-t-0 border-r-0 -rotate-45 mb-2" />
        </div>

        <h3 className="text-neutral-600 text-3xl font-bold text-center leading-tight mb-10">
          완료된 검사리포트를<br />제출합니다.
        </h3>

        <div className="flex gap-4 w-full justify-center">
          {/* 1. 아니오 (왼쪽, 회색) */}
          <button
            onClick={onClose}
            className="w-24 h-11 bg-slate-300 hover:bg-slate-400 text-white rounded font-bold transition-colors"
          >
            아니오
          </button>
          
          {/* 2. 네 (오른쪽, 보라색) */}
          <button
            onClick={onConfirm}
            className="w-24 h-11 bg-violet-400 hover:bg-violet-500 text-white rounded font-bold transition-colors"
          >
            네
          </button>
        </div>
      </div>
    </div>
  );
};

export default ReportSubmitModal;