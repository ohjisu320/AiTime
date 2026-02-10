import React, { useState, useEffect } from 'react'; // useState, useEffect 추가
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
  disableKeyboardOffset?: boolean; // 👈 키보드 오프셋 비활성화 (검사 페이지 등)
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
  hideCloseButton = false, // 👈 닫기 버튼 숨김
  disableKeyboardOffset = false // 👈 키보드 오프셋 기능 비활성화 옵션 추가
}: ConfirmModalProps & { closeOnConfirm?: boolean; disableKeyboardOffset?: boolean }) => {
  // 모바일 키보드 대응: Visual Viewport API로 키보드 높이 감지
  const [keyboardOffset, setKeyboardOffset] = useState(0);

  useEffect(() => {
    // 기능 비활성화 시 실행 안 함
    if (disableKeyboardOffset) {
      setKeyboardOffset(0);
      return;
    }

    // Visual Viewport API 지원 확인
    if (typeof window === 'undefined' || !window.visualViewport) return;

    const handleResize = () => {
      const visualViewport = window.visualViewport;
      if (!visualViewport) return;

      // 키보드 높이 계산: window.innerHeight - visualViewport.height
      const keyboardHeight = window.innerHeight - visualViewport.height;

      // 키보드가 150px 이상 올라왔을 때만 모달을 위로 이동
      if (keyboardHeight > 150) {
        // 모달을 키보드 높이의 절반만큼 위로 이동
        setKeyboardOffset(keyboardHeight / 2);
      } else {
        setKeyboardOffset(0);
      }
    };

    // 초기 체크
    handleResize();

    // 리사이즈 이벤트 리스너 등록
    window.visualViewport.addEventListener('resize', handleResize);
    window.visualViewport.addEventListener('scroll', handleResize);

    return () => {
      // 클린업
      if (window.visualViewport) {
        window.visualViewport.removeEventListener('resize', handleResize);
        window.visualViewport.removeEventListener('scroll', handleResize);
      }
    };
  }, [isOpen, disableKeyboardOffset]); // 의존성 추가

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

      <DialogContent
        className={cn(
          "fixed left-[50%] top-[50%] z-50 w-full max-w-[420px] translate-x-[-50%] translate-y-[-50%] rounded-3xl p-8 bg-white shadow-2xl border-none outline-none transition-transform duration-200",
          confirmVariant === 'rose' && "border-t-8 border-rose-500"
        )}
        style={
          disableKeyboardOffset ? undefined : {
            transform: `translate(-50%, calc(-50% - ${keyboardOffset}px))`
          }
        }
      >

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