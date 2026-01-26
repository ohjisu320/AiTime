import { useState } from 'react';
import { toast } from "sonner"; // 알림을 위해 추가

interface CodeRegisterProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: (inviteCode: string) => void; // 입력받은 코드를 전달하도록 수정
  title: string;
  description: string;
  confirmText: string;
  isDestructive?: boolean;
  childName?: string;
}

const CodeRegisterModal = ({ 
  isOpen, 
  onClose, 
  onConfirm, 
  title, 
  description, 
  confirmText, 
  isDestructive,
  childName 
}: CodeRegisterProps) => { // 타입을 CodeRegisterProps로 일치시킴

  const [inviteCode, setInviteCode] = useState(""); // Swagger input: inviteCode

  if (!isOpen) return null;

  const handleConfirm = () => {
    if (!inviteCode.trim()) {
      toast.error("초대 코드를 입력해 주세요.");
      return;
    }
    onConfirm(inviteCode); // 부모 컴포넌트(DashboardPage)로 코드 전달
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex justify-center items-center z-[100] p-4 backdrop-blur-sm">
      <div className={`bg-white p-8 rounded-3xl shadow-2xl text-center max-w-sm w-full ${isDestructive ? 'border-t-8 border-rose-500' : ''}`}>
        
        {/* 제목 및 설명 (childName 반영) */}
        <h2 className="text-xl font-bold mb-2 text-[#6366F1]">{title}</h2>
        <div className="text-gray-500 mb-6 text-sm leading-relaxed">
          <span className="font-bold text-gray-700">{childName}</span> {description}
        </div>

        {/* 초대 코드 입력창 추가 */}
        <div className="mb-6">
          <input
            type="text"
            placeholder="초대 코드 입력"
            value={inviteCode}
            onChange={(e) => setInviteCode(e.target.value.toUpperCase())}
            className="w-full h-14 text-center text-xl font-mono tracking-widest rounded-2xl border-2 border-indigo-50 bg-gray-50 focus:border-[#6366F1] focus:bg-white outline-none transition-all"
          />
        </div>

        {/* 버튼 영역 */}
        <div className="flex gap-3">
          <button 
            onClick={onClose} 
            className="flex-1 py-3 bg-gray-50 text-gray-500 rounded-xl font-semibold hover:bg-gray-100 transition-colors"
          >
            닫기
          </button>
          <button 
            onClick={handleConfirm} 
            className="flex-1 py-3 bg-[#6366F1] text-white rounded-xl font-semibold shadow-lg shadow-indigo-200 hover:bg-[#4F46E5] transition-colors"
          >
            {confirmText}
          </button>
        </div>
      </div>
    </div>
  );
};

export default CodeRegisterModal;