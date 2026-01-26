import { useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogOverlay, // 1. Overlay 컴포넌트 추가
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";

interface CodeRegisterModalProps {
  isOpen: boolean;
  onClose: () => void;
  childName: string;
}

const CodeRegisterModal = ({ isOpen, onClose, childName }: CodeRegisterModalProps) => {
  const [inviteCode, setInviteCode] = useState("");

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      {/* 2. 배경 오버레이 설정: 반투명 블랙 배경 적용 */}
      <DialogOverlay className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm" /> 
      
      <DialogContent className="fixed left-[50%] top-[50%] z-50 w-full max-w-[420px] translate-x-[-50%] translate-y-[-50%] rounded-3xl p-8 bg-white shadow-2xl border-none outline-none">
        <DialogHeader className="space-y-4 text-center">
          <DialogTitle className="text-2xl font-bold text-[#6366F1]">
            병원 초대 코드 등록
          </DialogTitle>
          <DialogDescription className="text-gray-500">
            <strong>{childName}</strong> 어린이의 검사 결과를 공유받을<br />
            병원 초대 코드를 입력해 주세요.
          </DialogDescription>
        </DialogHeader>

        <div className="py-8">
          <Input
            placeholder="초대 코드 입력"
            value={inviteCode}
            onChange={(e) => setInviteCode(e.target.value.toUpperCase())}
            className="h-16 text-center text-xl font-mono tracking-widest rounded-2xl border-2 border-indigo-100 bg-white focus-visible:ring-[#6366F1]"
          />
        </div>

        <DialogFooter>
          <Button
            className="w-full h-16 bg-[#6366F1] hover:bg-[#4F46E5] text-white text-lg font-bold rounded-2xl shadow-lg transition-all"
            onClick={() => {
              console.log({ inviteCode });
              toast.success("등록되었습니다.");
              onClose();
            }}
          >
            병원 연결하기
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};

export default CodeRegisterModal;