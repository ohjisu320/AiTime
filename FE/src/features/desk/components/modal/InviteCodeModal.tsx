import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

// 폼 입력용 데이터 타입 (화면용)
export interface InviteCodeFormState {
  childName: string;
  childBirthdate: string; // YYYY.MM.DD
  parentPhone: string; // 010-0000-0000
  visitDate: string; // [분리] YYYY.MM.DD
  visitTime: string; // [분리] HH:mm
}

// 최종 API 전송용 데이터 타입
export interface InviteCodeRequestData {
  childName: string;
  childBirthdate: string;
  parentPhone: string;
  scheduledAt: string; // 합쳐진 결과 (YYYY-MM-DDTHH:mm:ss)
}

interface InviteCodeModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: (data: InviteCodeRequestData) => void;
}

export default function InviteCodeModal({
  isOpen,
  onClose,
  onConfirm,
}: InviteCodeModalProps) {
  // --- State ---
  const [formData, setFormData] = useState<InviteCodeFormState>({
    childName: "",
    childBirthdate: "",
    parentPhone: "",
    visitDate: "",
    visitTime: "",
  });

  const [errorMessage, setErrorMessage] = useState("");

  // 모달이 열릴 때 상태 초기화
  useEffect(() => {
    if (isOpen) {
      setFormData({
        childName: "",
        childBirthdate: "",
        parentPhone: "",
        visitDate: "",
        visitTime: "",
      });
      setErrorMessage("");
    }
  }, [isOpen]);

  if (!isOpen) return null;

  // --- Auto Formatting Handlers ---

  // 날짜 포맷터 (YYYY.MM.DD)
  const formatDate = (value: string) => {
    const num = value.replace(/[^0-9]/g, "");
    if (num.length <= 4) return num;
    if (num.length <= 6) return `${num.slice(0, 4)}.${num.slice(4)}`;
    return `${num.slice(0, 4)}.${num.slice(4, 6)}.${num.slice(6, 8)}`;
  };

  // 전화번호 포맷터 (010-XXXX-XXXX)
  const formatPhone = (value: string) => {
    const num = value.replace(/[^0-9]/g, "");
    if (num.length <= 3) return num;
    if (num.length <= 7) return `${num.slice(0, 3)}-${num.slice(3)}`;
    return `${num.slice(0, 3)}-${num.slice(3, 7)}-${num.slice(7, 11)}`;
  };

  // 시간 포맷터 (HH:mm)
  const formatTime = (value: string) => {
    const num = value.replace(/[^0-9]/g, "");
    if (num.length <= 2) return num;
    return `${num.slice(0, 2)}:${num.slice(2, 4)}`;
  };

  // 통합 핸들러
  const handleChange = (field: keyof InviteCodeFormState, value: string) => {
    let formattedValue = value;

    if (field === "childBirthdate" || field === "visitDate") {
      formattedValue = formatDate(value);
    } else if (field === "parentPhone") {
      formattedValue = formatPhone(value);
    } else if (field === "visitTime") {
      formattedValue = formatTime(value);
    }

    setFormData((prev) => ({ ...prev, [field]: formattedValue }));
    if (errorMessage) setErrorMessage("");
  };

  // --- Validation ---
  const validateInputs = () => {
    const { childName, childBirthdate, parentPhone, visitDate, visitTime } =
      formData;

    if (!childName.trim()) return "환자 이름을 입력해주세요.";
    if (childBirthdate.length !== 10)
      return "생년월일 8자리를 모두 입력해주세요.";
    if (parentPhone.length < 12) return "올바른 휴대전화 번호를 입력해주세요.";
    if (visitDate.length !== 10) return "방문 예약일을 정확히 입력해주세요.";

    // 시간 검증 (HH:mm 길이 및 유효성)
    if (visitTime.length !== 5) return "방문 예약 시간을 입력해주세요.";
    const [hour, minute] = visitTime.split(":").map(Number);
    if (hour > 23 || minute > 59)
      return "올바른 시간을 입력해주세요 (00:00 ~ 23:59)";

    return "";
  };

  const handleSubmit = () => {
    const error = validateInputs();
    if (error) {
      setErrorMessage(error);
      return;
    }

    // 데이터 정제 및 병합 (API 포맷: ISO-8601)
    const formattedData: InviteCodeRequestData = {
      childName: formData.childName,
      // 2026.01.22 -> 2026-01-22
      childBirthdate: formData.childBirthdate.replace(/\./g, "-"),
      // 010-1234-5678 -> 01012345678
      parentPhone: formData.parentPhone.replace(/-/g, ""),
      // 날짜 + 시간 합치기: 2026-01-22T14:00:00
      scheduledAt: `${formData.visitDate.replace(/\./g, "-")}T${formData.visitTime}:00`,
    };

    onConfirm(formattedData);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm p-4 animate-in fade-in duration-200">
      <div className="bg-white w-full max-w-[500px] rounded-xl shadow-2xl overflow-hidden relative">
        <div className="pt-10 pb-6 text-center">
          <h2 className="text-3xl font-bold text-gray-800">초대 코드 발급</h2>
        </div>

        <div className="px-10 pb-10 space-y-5">
          {/* 1. 환자 이름 */}
          <div className="space-y-2">
            <label className="text-base font-bold text-gray-600">
              환자 이름
            </label>
            <Input
              placeholder="예: 김아이"
              value={formData.childName}
              onChange={(e) => handleChange("childName", e.target.value)}
              className="h-12 text-lg border-gray-300 focus-visible:ring-[#5A55D6]"
            />
          </div>

          {/* 2. 생년월일 */}
          <div className="space-y-2">
            <label className="text-base font-bold text-gray-600">
              생년월일 (YYYY.MM.DD)
            </label>
            <Input
              placeholder="예: 20260122"
              maxLength={10}
              value={formData.childBirthdate}
              onChange={(e) => handleChange("childBirthdate", e.target.value)}
              className="h-12 text-lg border-gray-300 focus-visible:ring-[#5A55D6]"
            />
          </div>

          {/* 3. 보호자 연락처 */}
          <div className="space-y-2">
            <label className="text-base font-bold text-gray-600">
              보호자 연락처
            </label>
            <Input
              placeholder="예: 01012345678"
              maxLength={13}
              value={formData.parentPhone}
              onChange={(e) => handleChange("parentPhone", e.target.value)}
              className="h-12 text-lg border-gray-300 focus-visible:ring-[#5A55D6]"
            />
          </div>

          {/* 4. 방문 예약일 (날짜 / 시간 분리) */}
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <label className="text-base font-bold text-gray-600">
                예약일
              </label>
              <Input
                placeholder="20260122"
                maxLength={10}
                value={formData.visitDate}
                onChange={(e) => handleChange("visitDate", e.target.value)}
                className="h-12 text-lg border-gray-300 focus-visible:ring-[#5A55D6]"
              />
            </div>
            <div className="space-y-2">
              <label className="text-base font-bold text-gray-600">시간</label>
              <Input
                placeholder="14:00"
                maxLength={5}
                value={formData.visitTime}
                onChange={(e) => handleChange("visitTime", e.target.value)}
                className="h-12 text-lg border-gray-300 focus-visible:ring-[#5A55D6]"
              />
            </div>
          </div>

          {/* 에러 메시지 & 버튼 */}
          <div className="mt-8 pt-2">
            <div className="h-6 mb-2 text-center">
              {errorMessage && (
                <p className="text-sm text-red-500 font-medium animate-pulse">
                  {errorMessage}
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
