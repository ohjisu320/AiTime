import { useState, useEffect } from "react";
// import { X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

// API 명세에 따른 요청 데이터 타입
export interface InviteCodeFormData {
  childName: string;
  childBirthdate: string; // YYYY-MM-DD 형식으로 변환 필요
  parentPhone: string;
}

interface InviteCodeModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: (data: InviteCodeFormData) => void;
}

export default function InviteCodeModal({
  isOpen,
  onClose,
  onConfirm,
}: InviteCodeModalProps) {
  // --- State ---
  const [formData, setFormData] = useState<InviteCodeFormData>({
    childName: "",
    childBirthdate: "",
    parentPhone: "",
  });

  const [errorMessage, setErrorMessage] = useState("");

  // 모달이 열릴 때 상태 초기화
  useEffect(() => {
    if (isOpen) {
      setFormData({ childName: "", childBirthdate: "", parentPhone: "" });
      setErrorMessage("");
    }
  }, [isOpen]);

  if (!isOpen) return null;

  // --- Handlers ---
  const handleChange = (field: keyof InviteCodeFormData, value: string) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
    if (errorMessage) setErrorMessage(""); // 입력 시 에러 메시지 초기화
  };

  const validateInputs = () => {
    const { childName, childBirthdate, parentPhone } = formData;

    if (!childName.trim()) return "환자 이름을 입력해주세요.";

    // 생년월일 간단 검증 (YYYY.MM.DD 또는 YYYYMMDD)
    const birthRegex =
      /^(19|20)\d{2}.?(0[1-9]|1[0-2]).?(0[1-9]|[12][0-9]|3[01])$/;
    if (!birthRegex.test(childBirthdate.replace(/[^0-9]/g, ""))) {
      return "올바른 생년월일 형식이 아닙니다. (예: 2026.01.22)";
    }

    // 휴대폰 번호 검증 (010-1234-5678 or 01012345678)
    const phoneRegex = /^01[0-9]-?[0-9]{3,4}-?[0-9]{4}$/;
    if (!phoneRegex.test(parentPhone)) {
      return "유효한 휴대전화 번호가 아닙니다.";
    }

    return "";
  };

  const handleSubmit = () => {
    const error = validateInputs();
    if (error) {
      setErrorMessage(error);
      return;
    }

    // 데이터 정제 (API 포맷에 맞게 변환: 2026.01.01 -> 2026-01-01)
    const formattedData = {
      ...formData,
      childBirthdate: formData.childBirthdate.replace(/\./g, "-"),
      parentPhone: formData.parentPhone.replace(/-/g, ""), // 하이픈 제거
    };

    onConfirm(formattedData);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm p-4 animate-in fade-in duration-200">
      {/* 모달 컨테이너 */}
      <div className="bg-white w-full max-w-[500px] rounded-xl shadow-2xl overflow-hidden relative">
        {/* 헤더 (타이틀) */}
        <div className="pt-10 pb-6 text-center">
          <h2 className="text-3xl font-bold text-gray-800">초대 코드 발급</h2>
        </div>

        {/* 닫기 버튼 (우측 상단, 필요시 주석 해제하여 사용) */}
        {/* <button onClick={onClose} className="absolute top-4 right-4 text-gray-400 hover:text-gray-600">
          <X className="w-6 h-6" />
        </button> */}

        {/* 입력 폼 영역 */}
        <div className="px-10 pb-10 space-y-6">
          {/* 환자 이름 */}
          <div className="space-y-2">
            <label className="text-base font-bold text-gray-600">
              환자 이름
            </label>
            <Input
              placeholder="예: 김아이"
              value={formData.childName}
              onChange={(e) => handleChange("childName", e.target.value)}
              className="h-12 text-lg bg-white border-gray-300 focus-visible:ring-[#5A55D6]"
            />
          </div>

          {/* 생년월일 */}
          <div className="space-y-2">
            <label className="text-base font-bold text-gray-600">
              생년월일
            </label>
            <Input
              placeholder="2026.01.22"
              maxLength={10}
              value={formData.childBirthdate}
              onChange={(e) => handleChange("childBirthdate", e.target.value)}
              className="h-12 text-lg bg-white border-gray-300 focus-visible:ring-[#5A55D6]"
            />
          </div>

          {/* 보호자 휴대전화번호 */}
          <div className="space-y-2">
            <label className="text-base font-bold text-gray-600">
              보호자 휴대전화번호
            </label>
            <Input
              placeholder="010-1234-5678"
              value={formData.parentPhone}
              onChange={(e) => handleChange("parentPhone", e.target.value)}
              className="h-12 text-lg bg-white border-gray-300 focus-visible:ring-[#5A55D6]"
            />
          </div>

          {/* 에러 메시지 및 버튼 영역 */}
          <div className="mt-8 pt-2">
            {/* 에러 메시지 (공간 확보를 위해 min-h 설정 가능) */}
            <div className="h-6 mb-2 text-center">
              {errorMessage && (
                <p className="text-sm text-gray-500 font-medium">
                  {errorMessage}
                  <span className="block text-xs text-red-500 mt-1">
                    발송에 실패했습니다.
                  </span>
                </p>
              )}
            </div>

            <div className="flex gap-3">
              <Button
                onClick={handleSubmit}
                className="flex-1 h-12 text-lg font-bold bg-[#5A55D6] hover:bg-[#4844b8] text-white rounded-lg transition-colors"
              >
                전송
              </Button>
              <Button
                onClick={onClose}
                className="flex-1 h-12 text-lg font-bold bg-gray-500 hover:bg-gray-600 text-white rounded-lg transition-colors"
              >
                취소
              </Button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
