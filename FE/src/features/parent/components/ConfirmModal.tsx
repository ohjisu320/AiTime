interface ConfirmModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
  title: string;
  description: string | React.ReactNode;
  confirmText: string;
  isDestructive?: boolean; // 빨간색 강조가 필요한 경우 (4단계 등)
}

const ConfirmModal = ({ isOpen, onClose, onConfirm, title, description, confirmText, isDestructive }: ConfirmModalProps) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/50 flex justify-center items-center z-[100] p-4">
      <div className={`bg-white p-8 rounded-3xl shadow-2xl text-center max-w-sm w-full ${isDestructive ? 'border-t-8 border-rose-500' : ''}`}>
        <h2 className="text-xl font-bold mb-2 text-gray-800">{title}</h2>
        <div className="text-gray-500 mb-6 text-sm leading-relaxed">{description}</div>
        <div className="flex gap-3">
          <button onClick={onClose} className="flex-1 py-3 bg-gray-50 text-gray-500 rounded-xl font-semibold hover:bg-gray-100 transition-colors">
            닫기
          </button>
          <button onClick={onConfirm} className="flex-1 py-3 bg-[#6366F1] text-white rounded-xl font-semibold shadow-lg shadow-indigo-200 hover:bg-[#4F46E5] transition-colors">
            {confirmText}
          </button>
        </div>
      </div>
    </div>
  );
};

export default ConfirmModal;