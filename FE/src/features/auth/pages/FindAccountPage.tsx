// src/features/auth/pages/FindAccountPage.tsx
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import Swal from "sweetalert2";
import { ArrowLeft, CheckCircle2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { cn } from "@/lib/utils";

// 화면 모드 타입 정의
type ViewMode = "MENU" | "FIND_ID" | "RESET_PW";

export default function FindAccountPage() {
  const navigate = useNavigate();

  // 현재 화면 모드 상태
  const [mode, setMode] = useState<ViewMode>("MENU");

  // --- 데이터 상태 (API 명세서 변수명 준수) ---
  const [phoneNumber, setPhoneNumber] = useState(""); // phone -> phoneNumber
  const [verificationCode, setVerificationCode] = useState(""); // authCode -> verificationCode

  // 비밀번호 변경용
  const [password, setPassword] = useState(""); // newPassword -> password
  const [confirmPassword, setConfirmPassword] = useState("");

  // --- 결과 데이터 (Mock) ---
  const [loginId, setLoginId] = useState(""); // foundId -> loginId
  const [userId, setUserId] = useState(""); // 비밀번호 변경 대상 userId

  // --- UI 상태 ---
  const [isCodeSent, setIsCodeSent] = useState(false);
  const [isVerified, setIsVerified] = useState(false);

  // ------------------------------------------
  // 핸들러 함수들 (Mock Logic)
  // ------------------------------------------

  // 초기화 및 모드 변경
  const handleModeChange = (newMode: ViewMode) => {
    setMode(newMode);
    setPhoneNumber("");
    setVerificationCode("");
    setIsCodeSent(false);
    setIsVerified(false);
    setLoginId("");
    setUserId("");
    setPassword("");
    setConfirmPassword("");
  };

  // 뒤로가기 핸들러
  const handleBack = () => {
    if (mode === "MENU") {
      navigate("/login");
    } else {
      handleModeChange("MENU");
    }
  };

  // 1. [Mock] 인증번호 요청
  const handleRequestAuthCode = () => {
    if (!phoneNumber) {
      Swal.fire({
        icon: "warning",
        text: "휴대전화번호를 입력해주세요.",
        confirmButtonColor: "#9593D9",
      });
      return;
    }

    // API 호출 흉내
    setIsCodeSent(true);
    Swal.fire({
      icon: "success",
      text: "인증번호가 발송되었습니다. (테스트: 1234)",
      confirmButtonColor: "#9593D9",
    });
  };

  // 2. [Mock] 인증번호 확인
  const handleVerifyAuthCode = () => {
    if (!verificationCode) {
      Swal.fire({
        icon: "warning",
        text: "인증번호를 입력해주세요.",
        confirmButtonColor: "#9593D9",
      });
      return;
    }

    // 테스트 코드 '1234'일 때만 성공
    if (verificationCode === "1234") {
      setIsVerified(true);
      Swal.fire({
        icon: "success",
        text: "인증이 완료되었습니다.",
        showConfirmButton: false,
        timer: 1000,
      });

      // 모드에 따라 결과 데이터 세팅 (Mock)
      if (mode === "FIND_ID") {
        setLoginId("aitime_parent"); // 찾은 아이디 예시
      } else if (mode === "RESET_PW") {
        setUserId("mock-user-uuid"); // 유저 식별자 예시
      }
    } else {
      Swal.fire({
        icon: "error",
        text: "인증번호가 일치하지 않습니다.",
        confirmButtonColor: "#9593D9",
      });
    }
  };

  // 3. [Mock] 비밀번호 변경
  const handlePasswordReset = () => {
    if (password.length < 8) {
      Swal.fire({
        icon: "warning",
        text: "비밀번호는 8자 이상이어야 합니다.",
        confirmButtonColor: "#9593D9",
      });
      return;
    }
    if (password !== confirmPassword) {
      Swal.fire({
        icon: "error",
        text: "비밀번호가 서로 일치하지 않습니다.",
        confirmButtonColor: "#9593D9",
      });
      return;
    }

    Swal.fire({
      icon: "success",
      title: "변경 완료",
      text: "비밀번호가 성공적으로 변경되었습니다.",
      confirmButtonColor: "#9593D9",
    }).then(() => {
      navigate("/login");
    });
  };

  // ------------------------------------------
  // UI 컴포넌트
  // ------------------------------------------

  return (
    <div className="min-h-screen w-full flex flex-col items-center justify-center bg-[#E3E0F5] relative p-6 overflow-y-auto">
      {/* 헤더 영역 */}
      <div className="w-full max-w-[1024px] h-20 relative flex items-center justify-center mb-6">
        <button
          onClick={handleBack}
          className="absolute left-0 top-1/2 -translate-y-1/2 flex items-center gap-3 text-gray-500 hover:text-[#9593D9] transition-colors"
        >
          <ArrowLeft className="w-6 h-6" />
          <span className="text-lg font-medium text-[#555555]">뒤로 가기</span>
        </button>

        <div className="flex items-center gap-4">
          <div className="w-12 h-12 bg-[#D9D9D9] rounded-2xl flex items-center justify-center shadow-sm" />
          <h1 className="text-5xl font-bold text-black font-['DM_Sans'] tracking-tight">
            AiTime
          </h1>
        </div>
      </div>

      {/* 메인 카드 컨테이너 */}
      <div className="w-full max-w-[1024px] bg-white rounded-[50px] shadow-[0_10px_40px_rgba(0,0,0,0.05)] p-12 md:p-20 mb-10 min-h-[600px] flex flex-col justify-center animate-fade-in">
        {/* CASE 1: 메뉴 선택 */}
        {mode === "MENU" && (
          <div className="flex flex-col gap-12">
            <h2 className="text-3xl font-bold text-center text-[#1A1A1A]">
              아이디 / 비밀번호 찾기
            </h2>
            <div className="flex flex-col md:flex-row gap-8">
              <button
                onClick={() => handleModeChange("FIND_ID")}
                className="flex-1 h-[320px] bg-[#F3F0FF] hover:bg-[#EBE6FF] rounded-[40px] flex flex-col items-center justify-center gap-6 transition-all hover:scale-[1.02] group shadow-sm hover:shadow-md"
              >
                <div className="w-24 h-24 bg-white rounded-full flex items-center justify-center shadow-sm text-3xl font-bold text-[#9593D9] group-hover:text-[#7a78b8]">
                  ID
                </div>
                <div className="text-center">
                  <h3 className="text-2xl font-bold text-[#333]">
                    아이디 찾기
                  </h3>
                  <p className="text-base text-gray-500 mt-3 leading-relaxed">
                    가입 시 등록한 휴대폰 번호로
                    <br />
                    아이디를 조회합니다.
                  </p>
                </div>
              </button>

              <button
                onClick={() => handleModeChange("RESET_PW")}
                className="flex-1 h-[320px] bg-[#F3F0FF] hover:bg-[#EBE6FF] rounded-[40px] flex flex-col items-center justify-center gap-6 transition-all hover:scale-[1.02] group shadow-sm hover:shadow-md"
              >
                <div className="w-24 h-24 bg-white rounded-full flex items-center justify-center shadow-sm text-3xl font-bold text-[#9593D9] group-hover:text-[#7a78b8]">
                  PW
                </div>
                <div className="text-center">
                  <h3 className="text-2xl font-bold text-[#333]">
                    비밀번호 재설정
                  </h3>
                  <p className="text-base text-gray-500 mt-3 leading-relaxed">
                    본인 인증을 완료한 후 새로운
                    <br />
                    비밀번호로 변경합니다.
                  </p>
                </div>
              </button>
            </div>
          </div>
        )}

        {/* CASE 2: 아이디 찾기 */}
        {mode === "FIND_ID" && !loginId && (
          <div className="w-full max-w-[600px] mx-auto">
            <h2 className="text-3xl font-bold text-center text-[#1A1A1A] mb-12">
              아이디 찾기
            </h2>
            <div className="space-y-8">
              <div className="space-y-3">
                <Label className="text-lg font-bold text-[#333]">
                  휴대전화번호
                </Label>
                <div className="flex gap-3">
                  <Input
                    value={phoneNumber}
                    onChange={(e) => setPhoneNumber(e.target.value)}
                    placeholder="010-1234-5678"
                    className="flex-1 h-14 bg-gray-50 border-gray-200 rounded-2xl text-lg px-5"
                    disabled={isVerified}
                  />
                  <Button
                    onClick={handleRequestAuthCode}
                    disabled={isVerified}
                    className="h-14 w-[120px] bg-[#D6D3F0] hover:bg-[#c2bde6] text-[#5A5880] text-lg font-bold rounded-2xl shadow-none"
                  >
                    {isCodeSent ? "재전송" : "인증하기"}
                  </Button>
                </div>
              </div>

              {isCodeSent && (
                <div className="space-y-3 animate-fade-in">
                  <div className="flex gap-3">
                    <Input
                      value={verificationCode}
                      onChange={(e) => setVerificationCode(e.target.value)}
                      placeholder="인증번호 입력"
                      className="flex-1 h-14 bg-gray-50 border-gray-200 rounded-2xl text-lg px-5"
                      disabled={isVerified}
                    />
                    <Button
                      onClick={handleVerifyAuthCode}
                      disabled={isVerified}
                      className="h-14 w-[120px] bg-[#9593D9] hover:bg-[#8381c9] text-white text-lg font-bold rounded-2xl shadow-none"
                    >
                      확인
                    </Button>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* CASE 2-Result: 아이디 찾기 결과 */}
        {mode === "FIND_ID" && loginId && (
          <div className="w-full max-w-[600px] mx-auto text-center animate-fade-in">
            <h2 className="text-3xl font-bold text-[#1A1A1A] mb-14">
              아이디 찾기
            </h2>

            <div className="py-10">
              <p className="text-gray-500 text-xl mb-6">귀하의 아이디는</p>
              <div className="bg-[#F3F0FF] py-8 rounded-[30px] border border-[#9593D9]/20 shadow-sm">
                <span className="text-4xl font-bold text-[#9593D9] tracking-wide">
                  {loginId}
                </span>
              </div>
              <p className="text-gray-500 text-xl mt-6">입니다.</p>
            </div>

            <div className="flex flex-col gap-4 mt-10">
              <Button
                onClick={() => navigate("/login")}
                className="w-full h-16 bg-[#9593D9] hover:bg-[#8381c9] text-white text-xl font-bold rounded-2xl shadow-lg"
              >
                로그인하기
              </Button>
              <Button
                onClick={() => handleModeChange("RESET_PW")}
                className="w-full h-16 bg-[#D6D3F0] hover:bg-[#c2bde6] text-[#5A5880] text-xl font-bold rounded-2xl shadow-none"
              >
                비밀번호 재설정
              </Button>
            </div>
          </div>
        )}

        {/* CASE 3: 비밀번호 재설정 */}
        {mode === "RESET_PW" && (
          <div className="w-full max-w-[600px] mx-auto">
            <h2 className="text-3xl font-bold text-center text-[#1A1A1A] mb-12">
              비밀번호 재설정
            </h2>

            <div className="space-y-8">
              {/* 인증 섹션 */}
              <div className="space-y-6 pb-8 border-b border-gray-100">
                <div className="space-y-3">
                  <div className="flex justify-between items-end">
                    <Label className="text-lg font-bold text-[#333]">
                      휴대전화번호
                    </Label>
                    {isVerified && (
                      <span className="text-sm text-[#9593D9] font-bold flex items-center gap-1">
                        <CheckCircle2 className="w-4 h-4" />
                        인증 완료
                      </span>
                    )}
                  </div>
                  <div className="flex gap-3">
                    <Input
                      value={phoneNumber}
                      onChange={(e) => setPhoneNumber(e.target.value)}
                      placeholder="010-1234-5678"
                      className="flex-1 h-14 bg-gray-50 border-gray-200 rounded-2xl text-lg px-5"
                      disabled={isVerified}
                    />
                    <Button
                      onClick={handleRequestAuthCode}
                      disabled={isVerified}
                      className="h-14 w-[120px] bg-[#D6D3F0] hover:bg-[#c2bde6] text-[#5A5880] text-lg font-bold rounded-2xl shadow-none"
                    >
                      {isCodeSent ? "재전송" : "인증요청"}
                    </Button>
                  </div>
                </div>

                {isCodeSent && (
                  <div className="flex gap-3 animate-fade-in">
                    <Input
                      value={verificationCode}
                      onChange={(e) => setVerificationCode(e.target.value)}
                      placeholder="인증번호 입력"
                      className="flex-1 h-14 bg-gray-50 border-gray-200 rounded-2xl text-lg px-5"
                      disabled={isVerified}
                    />
                    <Button
                      onClick={handleVerifyAuthCode}
                      disabled={isVerified}
                      className="h-14 w-[120px] bg-[#9593D9] hover:bg-[#8381c9] text-white text-lg font-bold rounded-2xl shadow-none"
                    >
                      확인
                    </Button>
                  </div>
                )}
              </div>

              {/* 비밀번호 변경 섹션 */}
              {isVerified && (
                <div className="space-y-6 animate-fade-in pt-4">
                  <div className="space-y-3">
                    <Label className="text-lg font-bold text-[#333]">
                      새로운 비밀번호
                    </Label>
                    <Input
                      type="password"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      placeholder="새 비밀번호 입력"
                      className="h-14 bg-gray-50 border-gray-200 rounded-2xl text-lg px-5"
                    />
                  </div>
                  <div className="space-y-3">
                    <Label className="text-lg font-bold text-[#333]">
                      비밀번호 확인
                    </Label>
                    <Input
                      type="password"
                      value={confirmPassword}
                      onChange={(e) => setConfirmPassword(e.target.value)}
                      placeholder="비밀번호 재입력"
                      className="h-14 bg-gray-50 border-gray-200 rounded-2xl text-lg px-5"
                    />
                    {password &&
                      confirmPassword &&
                      password !== confirmPassword && (
                        <p className="text-sm text-red-500 pl-2">
                          비밀번호가 일치하지 않습니다.
                        </p>
                      )}
                  </div>

                  <Button
                    onClick={handlePasswordReset}
                    className="w-full h-16 bg-[#9593D9] hover:bg-[#8381c9] text-white text-xl font-bold rounded-2xl mt-8 shadow-lg"
                  >
                    비밀번호 변경
                  </Button>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
