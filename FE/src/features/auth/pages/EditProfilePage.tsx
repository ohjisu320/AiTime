import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import Swal from "sweetalert2";
import { ArrowLeft, CheckCircle2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

export default function EditProfilePage() {
  const navigate = useNavigate();

  // 단계: 'CHECK_PW'(비밀번호 확인) -> 'EDIT_FORM'(수정 폼)
  const [step, setStep] = useState<"CHECK_PW" | "EDIT_FORM">("CHECK_PW");

  // --- 상태 관리 ---
  const [currentPassword, setCurrentPassword] = useState(""); // Step 1용

  // Step 2용 데이터
  const [formData, setFormData] = useState({
    loginId: "",
    password: "", // 새 비밀번호
    confirmPassword: "", // 새 비밀번호 확인
    name: "",
    phoneNumber: "",
    verificationCode: "",
  });

  // UI 상태
  const [isChangingPassword, setIsChangingPassword] = useState(false); // 비밀번호 변경 모드 토글
  const [isCodeSent, setIsCodeSent] = useState(false); // 인증번호 발송 여부
  const [isVerified, setIsVerified] = useState(false); // 전화번호 인증 완료 여부

  // [Mock] 초기 데이터 로드 (Step 2 진입 시)
  useEffect(() => {
    if (step === "EDIT_FORM") {
      // API: GET /user/info (가정)
      setFormData((prev) => ({
        ...prev,
        loginId: "aitime_parent",
        name: "김싸피",
        phoneNumber: "010-1234-5678",
      }));
    }
  }, [step]);

  // --- 핸들러 ---

  // [Step 1] 비밀번호 확인
  const handleCheckPassword = () => {
    if (!currentPassword) {
      Swal.fire({
        icon: "warning",
        text: "비밀번호를 입력해주세요.",
        confirmButtonColor: "#9D8AD6",
      });
      return;
    }

    // [Mock] API: POST /user/check-password
    if (currentPassword === "1234") {
      setStep("EDIT_FORM");
    } else {
      Swal.fire({
        icon: "error",
        text: "비밀번호가 일치하지 않습니다. (테스트: 1234)",
        confirmButtonColor: "#9D8AD6",
      });
    }
  };

  // [Step 2] 인증번호 요청
  const handleRequestAuth = () => {
    if (!formData.phoneNumber) return;
    setIsCodeSent(true);
    Swal.fire({
      icon: "success",
      text: "인증번호가 발송되었습니다. (테스트: 1234)",
      confirmButtonColor: "#9D8AD6",
    });
  };

  // [Step 2] 인증번호 확인
  const handleVerifyAuth = () => {
    if (formData.verificationCode === "1234") {
      setIsVerified(true);
      Swal.fire({
        icon: "success",
        text: "인증되었습니다.",
        confirmButtonColor: "#9D8AD6",
      });
    } else {
      Swal.fire({
        icon: "error",
        text: "인증번호가 일치하지 않습니다.",
        confirmButtonColor: "#9D8AD6",
      });
    }
  };

  // [Step 2] 최종 수정 완료
  const handleSubmit = () => {
    if (isChangingPassword && formData.password !== formData.confirmPassword) {
      Swal.fire({
        icon: "warning",
        text: "새 비밀번호가 일치하지 않습니다.",
        confirmButtonColor: "#9D8AD6",
      });
      return;
    }

    // [Mock] API: PATCH /user/info
    Swal.fire({
      icon: "success",
      title: "수정 완료",
      text: "회원정보가 성공적으로 수정되었습니다.",
      confirmButtonColor: "#9D8AD6",
    }).then(() => {
      navigate("/parent/dashboard");
    });
  };

  // 입력 핸들러
  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  return (
    // ✨ 수정된 부분: min-h-screen -> min-h-full, overflow-y-auto 제거
    // MobileLayout 내부에서 이미 스크롤을 담당하므로, 여기서는 부모 높이에 맞추기만 하면 됩니다.
    <div className="w-full min-h-full flex flex-col items-center justify-center bg-[#E3E0F5] p-6">
      {/* 헤더 (뒤로가기) */}
      <div className="w-full max-w-[600px] h-20 relative flex items-center mb-2 shrink-0">
        <button
          onClick={() => navigate(-1)}
          className="flex items-center gap-2 text-gray-500 hover:text-[#9D8AD6] transition-colors"
        >
          <ArrowLeft className="w-5 h-5" />
          <span className="text-lg font-medium text-[#555555]">뒤로 가기</span>
        </button>
        <div className="flex items-center gap-2 ml-4">
          <div className="w-8 h-8 bg-[#9D8AD6] rounded-lg flex items-center justify-center text-white font-bold text-xs">
            Ai
          </div>
          <span className="text-xl font-bold text-black font-['DM_Sans']">
            AiTime
          </span>
        </div>
      </div>

      {/* 메인 카드 */}
      <div className="w-full max-w-[600px] bg-white rounded-[32px] shadow-lg p-8 md:p-12 mb-10 min-h-[500px] flex flex-col justify-center animate-fade-in shrink-0">
        {/* ======================================================= */}
        {/* CASE 1: 비밀번호 확인 (진입 전) */}
        {/* ======================================================= */}
        {step === "CHECK_PW" && (
          <div className="flex flex-col items-center text-center w-full">
            <h2 className="text-2xl font-bold text-[#1A1A1A] mb-4">
              회원정보 수정
            </h2>
            <p className="text-gray-500 mb-10 font-medium">
              회원정보를 수정하기 위해 비밀번호를 확인합니다
            </p>

            <div className="w-full text-left space-y-2 mb-8">
              <Label className="text-sm font-bold text-[#333]">비밀번호</Label>
              <Input
                type="password"
                value={currentPassword}
                onChange={(e) => setCurrentPassword(e.target.value)}
                placeholder="비밀번호 입력"
                className="h-12 bg-gray-50 border-gray-200 rounded-xl px-4 focus:border-[#9D8AD6]"
              />
            </div>

            <Button
              onClick={handleCheckPassword}
              className="w-full h-14 bg-[#9D8AD6] hover:bg-[#8381c9] text-white text-lg font-bold rounded-xl shadow-md"
            >
              확인
            </Button>
          </div>
        )}

        {/* ======================================================= */}
        {/* CASE 2: 회원정보 수정 폼 */}
        {/* ======================================================= */}
        {step === "EDIT_FORM" && (
          <div className="w-full">
            <h2 className="text-2xl font-bold text-[#1A1A1A] mb-8 border-b pb-4">
              회원정보 수정
            </h2>

            <div className="space-y-5">
              {/* 1. 아이디 (수정 불가) */}
              <div className="space-y-1">
                <Label className="text-sm font-bold text-[#333]">아이디</Label>
                <div className="flex gap-2">
                  <Input
                    name="loginId"
                    value={formData.loginId}
                    readOnly
                    className="flex-1 h-11 bg-gray-100 border-gray-200 rounded-lg text-sm px-3 text-gray-500 cursor-not-allowed"
                  />
                  <Button
                    disabled
                    className="h-11 w-[90px] bg-gray-200 text-gray-400 font-bold rounded-lg text-sm shadow-none"
                  >
                    중복확인
                  </Button>
                </div>
              </div>

              {/* 2. 비밀번호 (변경 모드 토글) */}
              <div className="space-y-1">
                <Label className="text-sm font-bold text-[#333]">
                  비밀번호
                </Label>

                {!isChangingPassword ? (
                  <>
                    <Input
                      type="password"
                      value="********"
                      readOnly
                      className="h-11 bg-gray-50 border-gray-200 rounded-lg text-sm px-3 mb-2"
                    />
                    <Button
                      onClick={() => setIsChangingPassword(true)}
                      className="w-full h-11 bg-[#9D8AD6] hover:bg-[#8381c9] text-white font-bold rounded-lg shadow-sm"
                    >
                      비밀번호 수정
                    </Button>
                  </>
                ) : (
                  <div className="space-y-2 animate-fade-in p-4 bg-gray-50 rounded-xl border border-gray-100">
                    <div className="space-y-1">
                      <Label className="text-xs text-gray-500">
                        새 비밀번호
                      </Label>
                      <Input
                        type="password"
                        name="password"
                        value={formData.password}
                        onChange={handleChange}
                        placeholder="8자 이상 입력"
                        className="h-11 bg-white border-gray-200 rounded-lg text-sm px-3 focus:border-[#9D8AD6]"
                      />
                    </div>
                    <div className="space-y-1">
                      <Label className="text-xs text-gray-500">
                        새 비밀번호 확인
                      </Label>
                      <Input
                        type="password"
                        name="confirmPassword"
                        value={formData.confirmPassword}
                        onChange={handleChange}
                        placeholder="비밀번호 재입력"
                        className="h-11 bg-white border-gray-200 rounded-lg text-sm px-3 focus:border-[#9D8AD6]"
                      />
                    </div>
                    <Button
                      onClick={() => {
                        setIsChangingPassword(false);
                        setFormData((prev) => ({
                          ...prev,
                          password: "",
                          confirmPassword: "",
                        }));
                      }}
                      variant="ghost"
                      className="w-full h-8 text-xs text-gray-400 hover:text-gray-600"
                    >
                      취소
                    </Button>
                  </div>
                )}
              </div>

              {/* 3. 보호자 이름 */}
              <div className="space-y-1">
                <Label className="text-sm font-bold text-[#333]">
                  보호자 이름
                </Label>
                <Input
                  name="name"
                  value={formData.name}
                  onChange={handleChange}
                  placeholder="이름 입력"
                  className="h-11 bg-white border-gray-200 rounded-lg text-sm px-3 focus:border-[#9D8AD6]"
                />
              </div>

              {/* 4. 휴대전화번호 & 인증 */}
              <div className="space-y-1">
                <div className="flex justify-between items-end mb-1">
                  <Label className="text-sm font-bold text-[#333]">
                    휴대전화번호
                  </Label>
                  {isVerified && (
                    <span className="text-xs text-[#9D8AD6] font-bold flex items-center gap-1">
                      <CheckCircle2 className="w-3 h-3" />
                      인증 완료
                    </span>
                  )}
                </div>

                <div className="flex gap-2">
                  <Input
                    type="tel"
                    name="phoneNumber"
                    value={formData.phoneNumber}
                    onChange={handleChange}
                    placeholder="010-1234-5678"
                    className="flex-1 h-11 bg-white border-gray-200 rounded-lg text-sm px-3 focus:border-[#9D8AD6]"
                    disabled={isVerified}
                  />
                  <Button
                    onClick={handleRequestAuth}
                    disabled={isVerified}
                    className="h-11 w-[90px] bg-[#D6D3F0] hover:bg-[#c2bde6] text-[#5A5880] font-bold rounded-lg text-sm shadow-none"
                  >
                    {isCodeSent ? "재전송" : "인증요청"}
                  </Button>
                </div>

                {isCodeSent && !isVerified && (
                  <div className="flex gap-2 mt-2 animate-fade-in">
                    <Input
                      type="text"
                      name="verificationCode"
                      value={formData.verificationCode}
                      onChange={handleChange}
                      placeholder="인증번호"
                      className="flex-1 h-11 bg-white border-gray-200 rounded-lg text-sm px-3 focus:border-[#9D8AD6]"
                    />
                    <Button
                      onClick={handleVerifyAuth}
                      className="h-11 w-[90px] bg-[#9D8AD6] hover:bg-[#8381c9] text-white font-bold rounded-lg text-sm shadow-none"
                    >
                      확인
                    </Button>
                  </div>
                )}
              </div>

              {/* 수정 완료 버튼 */}
              <Button
                onClick={handleSubmit}
                className="w-full h-14 bg-[#9D8AD6] hover:bg-[#8381c9] text-white text-lg font-bold rounded-xl shadow-md mt-6"
              >
                회원정보 수정 완료
              </Button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
