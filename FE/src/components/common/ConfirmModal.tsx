import React from 'react'; // ReactNode 사용을 위해 추가
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
import { cn } from "@/lib/utils";

interface ConfirmModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
  title: React.ReactNode;
  description?: string | React.ReactNode; // 👈 ? 추가 (선택 사항)
  confirmText?: string; // 👈 ? 추가 (선택 사항)
  confirmVariant?: 'violet' | 'rose' | 'slate';
  hideCloseButton?: boolean; // 👈 닫기 버튼 숨김 옵션 추가
}

const ConfirmModal = ({
  isOpen,
  onClose,
  onConfirm,
  title,
  description,
  confirmText = "확인",
  confirmVariant = 'violet',
  closeOnConfirm = true, // 👈 추가
  hideCloseButton = false // 👈 닫기 버튼 숨김
}: ConfirmModalProps & { closeOnConfirm?: boolean }) => {

  const variantStyles = {
    violet: 'bg-[#6366F1] hover:bg-[#4F46E5] shadow-indigo-100',
    rose: 'bg-rose-500 hover:bg-rose-600 shadow-rose-100',
    slate: 'bg-slate-500 hover:bg-slate-600 shadow-slate-100'
  };

  const titleStyles = {
    violet: 'text-[#6366F1]',
    rose: 'text-rose-500',
    slate: 'text-slate-600'
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogOverlay className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm" />

      <DialogContent className={cn(
        "fixed left-[50%] top-[50%] z-50 w-full max-w-[420px] translate-x-[-50%] translate-y-[-50%] rounded-3xl p-8 bg-white shadow-2xl border-none outline-none",
        confirmVariant === 'rose' && "border-t-8 border-rose-500"
      )}>

        <DialogHeader className="space-y-4 text-center">
          <DialogTitle className={cn("text-2xl font-bold whitespace-pre-wrap", titleStyles[confirmVariant])}>
            {title}
          </DialogTitle>
          <DialogDescription className="text-gray-500 text-base leading-relaxed">
            {description}
          </DialogDescription>
        </DialogHeader>

        <DialogFooter className="flex flex-row gap-3 mt-8">
          {!hideCloseButton && (
            <Button
              variant="ghost"
              className="flex-1 h-14 bg-gray-50 hover:bg-gray-100 text-gray-500 font-semibold rounded-2xl transition-all"
              onClick={onClose}
            >
              닫기
            </Button>
          )}
          <Button
            className={cn(
              "flex-1 h-14 text-white text-lg font-bold rounded-2xl shadow-lg transition-all",
              variantStyles[confirmVariant]
            )}
            onClick={() => {
              onConfirm();
              if (closeOnConfirm) onClose(); // 👈 조건부 실행
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