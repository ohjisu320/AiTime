import React from 'react';

interface RecheckModalProps {
  isOpen: boolean;
  missionTitle: string;
  onClose: () => void;
  onConfirm: () => void;
}

const RecheckModal: React.FC<RecheckModalProps> = ({ isOpen, missionTitle, onClose, onConfirm }) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/40 backdrop-blur-sm">
      <div className="w-[512px] bg-white rounded-2xl p-10 shadow-2xl flex flex-col items-center animate-in fade-in zoom-in duration-200">
        <div className="w-20 h-24 mb-6 border-4 border-green-600 rounded-xl flex items-center justify-center">
          <div className="w-10 h-7 border-4 border-green-600 border-t-0 border-r-0 -rotate-45 mb-2" />
        </div>

        <h3 className="text-neutral-600 text-3xl font-bold text-center leading-tight mb-10">
          {missionTitle} 검사를<br />다시 진행하시겠습니까?
        </h3>

        <div className="flex gap-4 w-full justify-center">
          {/* 1. 예 */}
          <button
            onClick={onConfirm}
            className="w-24 h-11 bg-slate-300 hover:bg-slate-400 text-white rounded-lg font-bold transition-colors"
          >
            예
          </button>
          
          {/* 2. 아니오 */}
          <button
            onClick={onClose}
            className="w-24 h-11 bg-violet-400 hover:bg-violet-500 text-white rounded-lg font-bold transition-colors"
          >
            아니오
          </button>
        </div>
      </div>
    </div>
  );
};

export default RecheckModal;