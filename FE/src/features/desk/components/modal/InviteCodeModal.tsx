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
  const [formData, setFormData] = useState<InviteCodeFormData & { doctorId?: string; scheduledAt: string }>({
    childName: "",
    childBirthdate: "",
    parentPhone: "",
    scheduledAt: "", // YYYY-MM-DDTHH:mm
    doctorId: "", // 선택된 의사 ID
  });

  const [doctors, setDoctors] = useState<{ id: string; name: string }[]>([]);
  const [errorMessage, setErrorMessage] = useState("");

  // 의사 목록 조회
  useEffect(() => {
    if (isOpen) {
      // 모달 열릴 때 초기화
      setFormData({
        childName: "",
        childBirthdate: "",
        parentPhone: "",
        scheduledAt: new Date().toISOString().slice(0, 16), // 현재 시간 기본값
        doctorId: ""
      });
      setErrorMessage("");

      // 의사 목록 로드
      import("@/features/desk/api/hospitalStaffApi").then(({ getDoctors }) => {
        getDoctors().then(response => {
          if (response.code === 200 && response.data) {
            setDoctors(response.data.map(d => ({ id: d.doctorId, name: d.doctorName })));
          } else { }
        }).catch(err => console.error("의사 목록 로드 실패", err));
      });
    }
  }, [isOpen]);

  if (!isOpen) return null;

  // --- Formatters ---
  const formatBirthdate = (val: string) => {
    const num = val.replace(/[^0-9]/g, "");
    if (num.length <= 4) return num;
    if (num.length <= 6) return `${num.slice(0, 4)}.${num.slice(4)}`;
    return `${num.slice(0, 4)}.${num.slice(4, 6)}.${num.slice(6, 8)}`; // YYYY.MM.DD
  };

  const formatPhone = (val: string) => {
    const num = val.replace(/[^0-9]/g, "");
    if (num.length <= 3) return num;
    if (num.length <= 7) return `${num.slice(0, 3)}-${num.slice(3)}`;
    return `${num.slice(0, 3)}-${num.slice(3, 7)}-${num.slice(7, 11)}`; // 010-1234-5678
  };

  // --- Handlers ---
  const handleChange = (field: keyof typeof formData, value: string) => {
    let formattedValue = value;
    if (field === "childBirthdate") formattedValue = formatBirthdate(value);
    if (field === "parentPhone") formattedValue = formatPhone(value);

    setFormData((prev) => ({ ...prev, [field]: formattedValue }));
    if (errorMessage) setErrorMessage("");
  };

  const validateInputs = () => {
    const { childName, childBirthdate, parentPhone, doctorId, scheduledAt } = formData;

    if (!childName.trim()) return "환자 이름을 입력해주세요.";

    if (childBirthdate.length < 10) return "생년월일을 모두 입력해주세요. (YYYY.MM.DD)";
    const birthRegex = /^(19|20)\d{2}.(0[1-9]|1[0-2]).(0[1-9]|[12][0-9]|3[01])$/;
    if (!birthRegex.test(childBirthdate)) return "올바른 생년월일 형식이 아닙니다.";

    if (parentPhone.length < 12) return "휴대전화 번호를 모두 입력해주세요.";

    // if (!doctorId) return "담당 의사를 선택해주세요."; // 의사 선택이 필수라면 주석 해제
    if (!scheduledAt) return "예약 일시를 선택해주세요.";

    return "";
  };

  const handleSubmit = () => {
    const error = validateInputs();
    if (error) {
      setErrorMessage(error);
      return;
    }

    // 데이터 정제 및 부모 컴포넌트로 전달
    const submittedData = {
      childName: formData.childName,
      childBirthdate: formData.childBirthdate, // 상위에서 . replace 처리
      parentPhone: formData.parentPhone,       // 상위에서 - replace 처리
      scheduledAt: new Date(formData.scheduledAt).toISOString(), // ISO 변환
      doctorId: formData.doctorId || undefined
    };

    onConfirm(submittedData as any);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm p-4 animate-in fade-in duration-200">
      <div className="bg-white w-full max-w-[500px] rounded-xl shadow-2xl overflow-hidden relative">
        <div className="pt-8 pb-4 text-center">
          <h2 className="text-2xl font-bold text-gray-800">초대 코드 발급</h2>
          <p className="text-sm text-gray-500 mt-1">환자 정보와 예약 일정을 입력해주세요</p>
        </div>

        <div className="px-8 pb-8 space-y-5">
          {/* 2열 레이아웃: 이름 / 생년월일 */}
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-1.5">
              <label className="text-sm font-bold text-gray-600">환자 이름</label>
              <Input
                placeholder="이름 입력"
                value={formData.childName}
                onChange={(e) => handleChange("childName", e.target.value)}
                className="h-10 border-gray-300 focus-visible:ring-[#5A55D6]"
              />
            </div>
            <div className="space-y-1.5">
              <label className="text-sm font-bold text-gray-600">생년월일</label>
              <Input
                placeholder="YYYY.MM.DD"
                maxLength={10}
                value={formData.childBirthdate}
                onChange={(e) => handleChange("childBirthdate", e.target.value)}
                className="h-10 border-gray-300 focus-visible:ring-[#5A55D6]"
              />
            </div>
          </div>

          {/* 연락처 */}
          <div className="space-y-1.5">
            <label className="text-sm font-bold text-gray-600">보호자 연락처</label>
            <Input
              placeholder="010-0000-0000"
              maxLength={13}
              value={formData.parentPhone}
              onChange={(e) => handleChange("parentPhone", e.target.value)}
              className="h-10 border-gray-300 focus-visible:ring-[#5A55D6]"
            />
          </div>

          {/* 2열 레이아웃: 담당의사 / 예약일시 */}
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-1.5">
              <label className="text-sm font-bold text-gray-600">담당 의사</label>
              <select
                className="w-full h-10 px-3 py-2 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-[#5A55D6] bg-white"
                value={formData.doctorId}
                onChange={(e) => handleChange("doctorId", e.target.value)}
              >
                <option value="">(선택 안함)</option>
                {doctors.map(doc => (
                  <option key={doc.id} value={doc.id}>{doc.name}</option>
                ))}
              </select>
            </div>
            <div className="space-y-1.5">
              <label className="text-sm font-bold text-gray-600">예약 일시</label>
              <Input
                type="datetime-local"
                value={formData.scheduledAt}
                onChange={(e) => handleChange("scheduledAt", e.target.value)}
                className="h-10 border-gray-300 focus-visible:ring-[#5A55D6] text-sm"
              />
            </div>
          </div>

          {/* 에러 메시지 */}
          <div className="min-h-[20px] text-center">
            {errorMessage && (
              <p className="text-xs text-red-500 font-bold">{errorMessage}</p>
            )}
          </div>

          <div className="flex gap-3 pt-2">
            <Button onClick={handleSubmit} className="flex-1 h-11 text-base font-bold bg-[#5A55D6] hover:bg-[#4844b8] text-white rounded-lg">
              발급하기
            </Button>
            <Button onClick={onClose} className="flex-1 h-11 text-base font-bold bg-gray-100 hover:bg-gray-200 text-gray-600 rounded-lg">
              취소
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
