import { useState } from "react";
import { X, AlertCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import type { ChildProfile } from "./ProfileCard";

interface DeleteProfileModalProps {
  targetProfile: ChildProfile | null;
  onClose: () => void;
  onConfirm: () => void;
}

export default function DeleteProfileModal({
  targetProfile,
  onClose,
  onConfirm,
}: DeleteProfileModalProps) {
  const [inputName, setInputName] = useState("");
  const CONFIRM_TEXT = "삭제"; // 확인을 위한 고정 텍스트

  if (!targetProfile) return null;

  const handleConfirm = () => {
    if (inputName !== CONFIRM_TEXT) return;
    onConfirm();
    setInputName("");
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm p-4">
      {/* 모달 크기 확대: max-w-lg */}
      <div className="bg-white w-full max-w-lg rounded-3xl shadow-2xl p-8 text-center animate-in zoom-in-95 duration-200">
        <div className="flex justify-end">
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
          >
            <X className="w-8 h-8" />
          </button>
        </div>

        <div className="flex flex-col items-center justify-center mb-6">
          {/* 아이콘 크기 확대 */}
          <div className="w-20 h-20 rounded-full bg-orange-100 flex items-center justify-center text-orange-500 mb-6">
            <AlertCircle className="w-10 h-10" />
          </div>

          <h2 className="text-2xl font-bold text-gray-800 leading-tight mb-2">
            아이의 정보를 삭제하면
            <br />
            복구할 수 없습니다.
          </h2>

          <p className="text-base text-gray-500 mt-2 mb-8">
            삭제를 원하시면 아래 입력창에
            <br />
            <span className="font-bold text-orange-500">'{CONFIRM_TEXT}'</span>
            를 입력해주세요
          </p>

          {/* 삭제 대상 프로필 미리보기 확대 */}
          <div className="flex flex-col items-center gap-3 mb-8 opacity-90">
            <div
              className={`w-24 h-24 rounded-full flex items-center justify-center text-5xl ${
                targetProfile.gender === "MALE" ? "bg-blue-200" : "bg-pink-200"
              }`}
            >
              {targetProfile.gender === "MALE" ? "👦" : "👧"}
            </div>
            <div className="text-xl font-bold text-gray-800">
              {targetProfile.name}
            </div>
            <div className="text-base text-gray-500">
              {targetProfile.months}개월
            </div>
          </div>

          {/* 입력창 확대 */}
          <Input
            placeholder={CONFIRM_TEXT}
            value={inputName}
            onChange={(e) => setInputName(e.target.value)}
            className="h-14 text-xl text-center bg-gray-50 border-gray-200 focus-visible:ring-red-400 mb-6"
          />

          {/* 버튼 확대 */}
          <Button
            onClick={handleConfirm}
            disabled={inputName !== CONFIRM_TEXT}
            className={`w-full h-14 text-xl font-bold rounded-xl ${
              inputName === CONFIRM_TEXT
                ? "bg-[#9D8AD6] hover:bg-[#8673c4] text-white"
                : "bg-gray-200 text-gray-400 cursor-not-allowed"
            }`}
          >
            확인
          </Button>
        </div>
      </div>
    </div>
  );
}
