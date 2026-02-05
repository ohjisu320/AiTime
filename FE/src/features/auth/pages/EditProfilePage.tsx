import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import Swal from "sweetalert2";
import { ArrowLeft, CheckCircle2, UserX, Save } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

// [API Imports]
import { getMyInfo, updateMyInfo, withdrawUser } from "../api/user/userApi";
import {
  sendPhoneVerification,
  verifyPhoneCode,
} from "../api/signup/signupApi";
import { resetPassword } from "../api/recovery/recoveryApi";

export default function EditProfilePage() {
  const navigate = useNavigate();

  // 단계: 'CHECK_PW'(비밀번호 확인) -> 'EDIT_FORM'(수정 폼)
  const [step, setStep] = useState<"CHECK_PW" | "EDIT_FORM">("CHECK_PW");

  // --- 상태 관리 ---
  const [userId, setUserId] = useState("");
  const [currentPassword, setCurrentPassword] = useState("");

  // Step 2용 데이터
  const [formData, setFormData] = useState({
    loginId: "",
    password: "",
    confirmPassword: "",
    name: "",
    phoneNumber: "",
    verificationCode: "",
  });

  // UI 상태
  const [isChangingPassword, setIsChangingPassword] = useState(false);
  const [isCodeSent, setIsCodeSent] = useState(false);
  const [isVerified, setIsVerified] = useState(false);
  const [loading, setLoading] = useState(false);

  // 초기 데이터 로드
  useEffect(() => {
    const fetchData = async () => {
      try {
        const data = await getMyInfo();
        setUserId(data.userId);
        setFormData((prev) => ({
          ...prev,
          loginId: data.loginId,
          name: data.name,
          phoneNumber: data.phoneNumber,
        }));
      } catch (error) {
        console.error("정보 로드 실패:", error);
      }
    };
    fetchData();
  }, []);

  // --- 핸들러 ---

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));

    if (name === "phoneNumber") {
      setIsVerified(false);
      setIsCodeSent(false);
    }
  };

  const handleCheckPassword = async () => {
    if (!currentPassword) {
      return Swal.fire("입력 필요", "현재 비밀번호를 입력해주세요.", "warning");
    }
    setStep("EDIT_FORM");
  };

  const handleRequestAuth = async () => {
    if (!/^010[0-9]{8}$/.test(formData.phoneNumber)) {
      return Swal.fire(
        "형식 오류",
        "'-' 없이 010으로 시작하는 숫자만 입력해주세요.",
        "warning",
      );
    }
    try {
      await sendPhoneVerification(formData.phoneNumber);
      setIsCodeSent(true);
      Swal.fire("발송 완료", "인증번호가 발송되었습니다.", "success");
    } catch (error) {
      Swal.fire("오류", "인증번호 발송에 실패했습니다.", "error");
    }
  };

  const handleVerifyAuth = async () => {
    if (!formData.verificationCode)
      return Swal.fire("입력 필요", "인증번호를 입력해주세요.", "warning");

    try {
      const isOk = await verifyPhoneCode(
        formData.phoneNumber,
        formData.verificationCode,
      );
      if (isOk) {
        setIsVerified(true);
        Swal.fire("성공", "휴대폰 인증이 완료되었습니다.", "success");
      } else {
        Swal.fire("실패", "인증번호가 일치하지 않습니다.", "error");
      }
    } catch (error) {
      Swal.fire("오류", "인증 확인 중 오류가 발생했습니다.", "error");
    }
  };

  const handleSubmit = async () => {
    if (!formData.name.trim())
      return Swal.fire("경고", "이름을 입력해주세요.", "warning");

    if (isCodeSent && !isVerified) {
      return Swal.fire("경고", "휴대폰 인증을 완료해주세요.", "warning");
    }

    if (isChangingPassword) {
      if (formData.password !== formData.confirmPassword) {
        return Swal.fire(
          "불일치",
          "새 비밀번호가 일치하지 않습니다.",
          "warning",
        );
      }
      if (formData.password.length < 4) {
        return Swal.fire(
          "경고",
          "비밀번호는 4자리 이상이어야 합니다.",
          "warning",
        );
      }
    }

    try {
      setLoading(true);

      await updateMyInfo({
        name: formData.name,
        phoneNumber: formData.phoneNumber,
      });

      if (isChangingPassword && formData.password) {
        await resetPassword(userId, formData.password);
      }

      await Swal.fire({
        icon: "success",
        title: "수정 완료",
        text: "회원 정보가 성공적으로 수정되었습니다.",
        confirmButtonColor: "#9593D9",
      });

      navigate("/parent/select-profile");
    } catch (error) {
      console.error(error);
      Swal.fire("실패", "정보 수정 중 오류가 발생했습니다.", "error");
    } finally {
      setLoading(false);
    }
  };

  const handleWithdraw = async () => {
    const result = await Swal.fire({
      title: "정말 탈퇴하시겠습니까?",
      text: "탈퇴 시 모든 데이터가 삭제되며 복구할 수 없습니다.",
      icon: "warning",
      showCancelButton: true,
      confirmButtonColor: "#d33",
      cancelButtonColor: "#3085d6",
      confirmButtonText: "탈퇴하기",
      cancelButtonText: "취소",
    });

    if (result.isConfirmed) {
      try {
        await withdrawUser();
        localStorage.clear();
        await Swal.fire("탈퇴 완료", "이용해주셔서 감사합니다.", "success");
        navigate("/login");
      } catch (error) {
        Swal.fire("오류", "탈퇴 처리에 실패했습니다.", "error");
      }
    }
  };

  // --- 렌더링 ---

  return (
    <div className="min-h-screen bg-[#F9F9FB] flex flex-col items-center p-4">
      {/* 헤더 */}
      <div className="w-full max-w-[600px] flex items-center justify-between mt-4 mb-8 z-10">
        <button
          onClick={() =>
            step === "EDIT_FORM" ? setStep("CHECK_PW") : navigate(-1)
          }
          className="flex items-center text-gray-600 hover:text-[#9593D9] transition-colors"
        >
          <ArrowLeft className="w-6 h-6 mr-1" />
          <span className="font-bold">뒤로가기</span>
        </button>
        <h1 className="text-xl font-bold text-[#1A1A1A]">
          {step === "CHECK_PW" ? "비밀번호 확인" : "내 정보 수정"}
        </h1>
        <div className="w-6" />
      </div>

      {/* Step 1: 비밀번호 확인 (중앙 정렬) */}
      {step === "CHECK_PW" && (
        <div className="flex-1 w-full flex items-center justify-center -mt-20">
          <div className="w-full max-w-[600px] bg-white rounded-[32px] shadow-lg p-10 md:p-12 animate-fade-in-up">
            <div className="text-center mb-10">
              <div className="w-20 h-20 bg-[#F0F0FF] rounded-full flex items-center justify-center text-[#9593D9] mx-auto mb-6">
                <CheckCircle2 className="w-10 h-10" />
              </div>
              <h2 className="text-2xl font-bold text-[#1A1A1A] mb-2">
                본인 확인
              </h2>
              <p className="text-gray-500 text-lg">
                소중한 개인정보 보호를 위해
                <br />
                비밀번호를 확인해주세요.
              </p>
            </div>

            <div className="space-y-6">
              <div className="space-y-2">
                <Label className="text-base font-bold text-gray-700">
                  비밀번호
                </Label>
                <Input
                  type="password"
                  value={currentPassword}
                  onChange={(e) => setCurrentPassword(e.target.value)}
                  placeholder="현재 비밀번호를 입력하세요"
                  className="h-14 border-gray-300 focus:border-[#9593D9] text-lg px-4"
                  onKeyDown={(e) => e.key === "Enter" && handleCheckPassword()}
                />
              </div>
              <Button
                onClick={handleCheckPassword}
                className="w-full h-14 bg-[#9593D9] hover:bg-[#8381c7] text-white font-bold text-xl rounded-xl shadow-md transition-transform active:scale-[0.98]"
              >
                확인
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Step 2: 수정 폼 (크기 키우고 중앙 정렬) */}
      {step === "EDIT_FORM" && (
        <div className="flex-1 w-full flex items-center justify-center my-4">
          <div className="w-full max-w-[600px] bg-white rounded-[32px] shadow-lg p-8 md:p-10 animate-fade-in-up">
            <div className="space-y-6">
              {/* 아이디 */}
              <div className="space-y-1">
                <Label className="text-sm font-bold text-gray-600">
                  아이디
                </Label>
                <Input
                  value={formData.loginId}
                  disabled
                  className="bg-gray-50 text-gray-500 border-gray-200 cursor-not-allowed h-12"
                />
              </div>

              {/* 비밀번호 변경 토글 */}
              <div className="border rounded-2xl p-5 border-gray-200">
                <div className="flex items-center justify-between mb-2">
                  <Label className="text-sm font-bold text-gray-700">
                    비밀번호
                  </Label>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setIsChangingPassword(!isChangingPassword)}
                    className="text-[#9593D9] hover:text-[#8381c7] hover:bg-[#F0F0FF] h-9 px-4 text-xs font-bold rounded-lg"
                  >
                    {isChangingPassword ? "변경 취소" : "변경하기"}
                  </Button>
                </div>

                {isChangingPassword && (
                  <div className="space-y-3 animate-fade-in mt-3">
                    <Input
                      type="password"
                      name="password"
                      value={formData.password}
                      onChange={handleChange}
                      placeholder="새 비밀번호"
                      className="h-12 border-gray-300 focus:border-[#9593D9]"
                    />
                    <Input
                      type="password"
                      name="confirmPassword"
                      value={formData.confirmPassword}
                      onChange={handleChange}
                      placeholder="새 비밀번호 확인"
                      className="h-12 border-gray-300 focus:border-[#9593D9]"
                    />
                  </div>
                )}
              </div>

              {/* 이름 */}
              <div className="space-y-1">
                <Label className="text-sm font-bold text-gray-700">이름</Label>
                <Input
                  name="name"
                  value={formData.name}
                  onChange={handleChange}
                  placeholder="이름 입력"
                  className="h-14 border-gray-300 focus:border-[#9593D9]"
                />
              </div>

              {/* 전화번호 & 인증 */}
              <div className="space-y-1">
                <Label className="text-sm font-bold text-gray-700">
                  휴대전화번호
                </Label>
                <div className="flex gap-2">
                  <Input
                    name="phoneNumber"
                    value={formData.phoneNumber}
                    onChange={handleChange}
                    placeholder="01012345678"
                    maxLength={11}
                    className="flex-1 h-14 border-gray-300 focus:border-[#9593D9]"
                  />
                  <Button
                    onClick={handleRequestAuth}
                    disabled={isVerified}
                    className="h-14 w-[100px] bg-[#D6D3F0] hover:bg-[#c2bde6] text-[#5A5880] font-bold rounded-xl text-sm shadow-none"
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
                      className="flex-1 h-12 bg-white border-gray-200 rounded-lg text-sm px-3 focus:border-[#9593D9]"
                    />
                    <Button
                      onClick={handleVerifyAuth}
                      className="h-12 w-[100px] bg-[#9593D9] hover:bg-[#8381c9] text-white font-bold rounded-lg text-sm shadow-none"
                    >
                      확인
                    </Button>
                  </div>
                )}
                {isVerified && (
                  <p className="text-sm text-green-600 font-bold mt-2 ml-1">
                    * 인증이 완료되었습니다.
                  </p>
                )}
              </div>

              {/* 수정 완료 버튼 */}
              <Button
                onClick={handleSubmit}
                disabled={loading}
                className="w-full h-14 bg-[#9593D9] hover:bg-[#8381c9] text-white text-xl font-bold rounded-xl shadow-md mt-6 transition-transform active:scale-[0.98]"
              >
                <Save className="w-6 h-6 mr-2" />
                {loading ? "저장 중..." : "수정 완료"}
              </Button>
            </div>

            <div className="w-full h-[1px] bg-gray-100 my-8"></div>

            <div className="flex justify-center flex-col items-center gap-2">
              <div className="w-12 h-12 bg-gray-100 rounded-full flex items-center justify-center text-gray-400 mb-1">
                <UserX className="w-6 h-6" />
              </div>
              <button
                onClick={handleWithdraw}
                className="text-sm text-gray-400 underline hover:text-red-500 transition-colors font-medium"
              >
                회원 탈퇴하기
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
