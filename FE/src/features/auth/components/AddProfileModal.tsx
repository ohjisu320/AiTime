import { useState } from "react";
import { X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

// 폼 데이터 타입
export interface AddProfileFormData {
  name: string;
  birthdate: string;
  gender: string;
}

interface AddProfileModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: (data: AddProfileFormData) => void;
}

export default function AddProfileModal({
  isOpen,
  onClose,
  onConfirm,
}: AddProfileModalProps) {
  const [form, setForm] = useState<AddProfileFormData>({
    name: "",
    birthdate: "",
    gender: "",
  });

  // 에러 메시지 상태 추가
  const [errorMessage, setErrorMessage] = useState("");

  if (!isOpen) return null;

  // 입력 값이 변경될 때 에러 메시지를 초기화하는 헬퍼 함수
  const handleChange = (field: keyof AddProfileFormData, value: string) => {
    setForm((prev) => ({ ...prev, [field]: value }));
    if (errorMessage) setErrorMessage(""); // 사용자가 수정하면 에러 문구 삭제
  };

  const handleSubmit = () => {
    // 유효성 검사
    if (!form.name || !form.birthdate || !form.gender) {
      setErrorMessage("모든 정보를 입력해주세요."); // alert 대신 상태 업데이트
      return;
    }
    onConfirm(form);
    setForm({ name: "", birthdate: "", gender: "" });
    setErrorMessage(""); // 초기화
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm p-4">
      <div className="bg-white w-full max-w-lg rounded-3xl shadow-2xl p-8 animate-in zoom-in-95 duration-200">
        <div className="flex justify-between items-center mb-8">
          <h2 className="text-2xl font-bold text-gray-800">아이 프로필 등록</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
          >
            <X className="w-8 h-8" />
          </button>
        </div>

        <div className="space-y-6">
          <div className="space-y-2">
            <label className="text-sm md:text-base font-bold text-gray-500">
              아이 이름
            </label>
            <Input
              placeholder="홍길동"
              value={form.name}
              onChange={(e) => handleChange("name", e.target.value)}
              className="h-14 text-lg bg-gray-50 border-gray-200 focus-visible:ring-[#5A55D6]"
            />
          </div>

          <div className="space-y-2">
            <label className="text-sm md:text-base font-bold text-gray-500">
              아이 생년월일
            </label>
            <Input
              placeholder="2026.01.01"
              value={form.birthdate}
              onChange={(e) => handleChange("birthdate", e.target.value)}
              className="h-14 text-lg bg-gray-50 border-gray-200 focus-visible:ring-[#5A55D6]"
            />
          </div>

          <div className="space-y-2">
            <label className="text-sm md:text-base font-bold text-gray-500">
              아이 성별
            </label>
            <Select onValueChange={(val) => handleChange("gender", val)}>
              <SelectTrigger className="h-14 text-lg bg-gray-50 border-gray-200 text-gray-600">
                <SelectValue placeholder="성별" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="MALE" className="text-lg py-3">
                  남자
                </SelectItem>
                <SelectItem value="FEMALE" className="text-lg py-3">
                  여자
                </SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* 에러 메시지 및 버튼 영역 */}
          <div className="mt-6">
            {errorMessage && (
              <div className="text-red-500 text-center font-bold mb-3 animate-pulse">
                {errorMessage}
              </div>
            )}

            <Button
              onClick={handleSubmit}
              className="w-full h-14 text-xl bg-[#9D8AD6] hover:bg-[#8673c4] text-white font-bold rounded-xl"
            >
              확인
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
