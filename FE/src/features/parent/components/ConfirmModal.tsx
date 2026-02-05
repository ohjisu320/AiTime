import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogOverlay,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";

interface ConfirmModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
  title: string;
  description: string | React.ReactNode;
  confirmText: string;
  isDestructive?: boolean; // 빨간색 강조가 필요한 경우
}

const ConfirmModal = ({ 
  isOpen, 
  onClose, 
  onConfirm, 
  title, 
  description, 
  confirmText, 
  isDestructive 
}: ConfirmModalProps) => {
  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      {/* 1. 배경 오버레이: CodeRegisterModal과 동일하게 적용 */}
      <DialogOverlay className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm" /> 
      
      <DialogContent className={`fixed left-[50%] top-[50%] z-50 w-full max-w-[420px] translate-x-[-50%] translate-y-[-50%] rounded-3xl p-8 bg-white shadow-2xl border-none outline-none ${isDestructive ? 'border-t-8 border-rose-500' : ''}`}>
        
        <DialogHeader className="space-y-4 text-center">
          {/* 2. 타이틀 스타일: isDestructive일 경우 로즈 색상으로 강조 */}
          <DialogTitle className={`text-2xl font-bold ${isDestructive ? 'text-rose-500' : 'text-[#6366F1]'}`}>
            {title}
          </DialogTitle>
          <DialogDescription className="text-gray-500 text-base leading-relaxed">
            {description}
          </DialogDescription>
        </DialogHeader>

        {/* 3. 푸터 버튼 구성: 닫기와 확인 버튼 가로 배치 */}
        <DialogFooter className="flex flex-row gap-3 mt-8">
          <Button
            variant="ghost"
            className="flex-1 h-14 bg-gray-50 hover:bg-gray-100 text-gray-500 font-semibold rounded-2xl transition-all"
            onClick={onClose}
          >
            닫기
          </Button>
          <Button
            className={`flex-1 h-14 text-white text-lg font-bold rounded-2xl shadow-lg transition-all ${
              isDestructive 
                ? 'bg-rose-500 hover:bg-rose-600 shadow-rose-100' 
                : 'bg-[#6366F1] hover:bg-[#4F46E5] shadow-indigo-100'
            }`}
            onClick={() => {
              onConfirm();
              onClose();
            }}
          >
            {confirmText}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};

export default ConfirmModal;