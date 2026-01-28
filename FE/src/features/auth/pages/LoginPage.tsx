// src/features/auth/pages/LoginPage.tsx
import { useState } from "react";
import { useForm } from "react-hook-form";
import { Link, useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { cn } from "@/lib/utils";
import { Loader2 } from "lucide-react";

// ---------------------------
// 1. 타입 정의
// ---------------------------
type TabType = "PARENT" | "DOCTOR" | "DESK";

// ✅ API 명세서 (UserLoginRequest, StaffLoginRequest)와 일치합니다.
interface LoginFormInputs {
  loginId: string;
  password: string;
}

// ---------------------------
// 2. 메인 컴포넌트
// ---------------------------
const LoginPage = () => {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState<TabType>("PARENT");
  const [isLoading, setIsLoading] = useState(false);

  const { register, handleSubmit } = useForm<LoginFormInputs>();

  const onSubmit = async (data: LoginFormInputs) => {
    setIsLoading(true);
    
    // ------------------------------------------------------------
    // [API 명세 준수 체크]
    // 1. 부모 로그인: POST /api/v1/user/login
    // 2. 의료진/데스크 로그인: POST /api/v1/hospital-staff/login
    // * 요청 바디(loginId, password)는 두 API 모두 동일하므로 현재 폼 구조가 맞습니다.
    // ------------------------------------------------------------
    console.log(`[${activeTab}] 로그인 시도:`, data);

    // Mock: 로그인 성공 시뮬레이션
    setTimeout(() => {
      setIsLoading(false);

      if (activeTab === "PARENT") navigate("/parent/select-profile");
      else if (activeTab === "DOCTOR") navigate("/doctor/dashboard");
      else navigate("/reception/dashboard");
    }, 1500);
  };

  return (
    <div className="min-h-screen w-full flex flex-col p-8 md:p-12 bg-[#E3E0F5] relative overflow-hidden">
      {/* --- Logo Area --- */}
      <div className="z-10 self-center mb-auto mt-4 md:mt-8">
        <div className="flex flex-col items-center gap-4">
          <div className="w-20 h-20 bg-[#D9D9D9] rounded-3xl shadow-sm" />
          <h1 className="text-6xl font-bold text-black font-['DM_Sans'] tracking-tight">
            AiTime
          </h1>
        </div>
      </div>

      {/* --- Main Card --- */}
      <motion.div
        initial={{ opacity: 0, y: 40, x: 20 }}
        animate={{ opacity: 1, y: 0, x: 0 }}
        transition={{ duration: 0.6, ease: "easeOut" }}
        className="w-full max-w-[760px] self-end bg-white rounded-[50px] shadow-[0px_10px_40px_rgba(149,147,217,0.4)] p-10 z-20"
      >
        <form onSubmit={handleSubmit(onSubmit)} className="w-full">
          {/* 1. 탭 영역 */}
          <div className="flex justify-end mb-6">
            <div className="flex gap-2 bg-transparent">
              <TabButton
                label="부모"
                isActive={activeTab === "PARENT"}
                onClick={() => setActiveTab("PARENT")}
              />
              <TabButton
                label="의료진"
                isActive={activeTab === "DOCTOR"}
                onClick={() => setActiveTab("DOCTOR")}
              />
              <TabButton
                label="접수처"
                isActive={activeTab === "DESK"}
                onClick={() => setActiveTab("DESK")}
              />
            </div>
          </div>

          {/* 구분선 */}
          <div className="w-full h-[1px] bg-slate-200 mb-8" />

          {/* 2. 입력 & 버튼 그리드 */}
          <div className="flex flex-col md:flex-row gap-6 md:gap-8">
            {/* 왼쪽 열: 입력 필드 */}
            <div className="flex-1 space-y-5">
              <div className="space-y-2">
                <label className="block text-lg font-bold text-black ml-1">
                  아이디
                </label>
                <input
                  {...register("loginId", { required: true })}
                  type="text"
                  placeholder="아이디를 입력하세요"
                  className={cn(
                    "w-full h-[64px] bg-gray-100 rounded-3xl px-6 text-lg border-2 border-transparent focus:border-[#9593D9] focus:bg-white transition-all outline-none placeholder:text-gray-400"
                  )}
                />
              </div>

              <div className="space-y-2">
                <label className="block text-lg font-bold text-black ml-1">
                  비밀번호
                </label>
                <input
                  {...register("password", { required: true })}
                  type="password"
                  placeholder="비밀번호를 입력하세요"
                  className={cn(
                    "w-full h-[64px] bg-gray-100 rounded-3xl px-6 text-lg border-2 border-transparent focus:border-[#9593D9] focus:bg-white transition-all outline-none placeholder:text-gray-400"
                  )}
                />
              </div>

              <div className="flex justify-end pt-1">
                <Link
                  to="/find-account"
                  className="text-[#9593D9] text-sm font-bold hover:text-[#7a78b8] transition-colors"
                >
                  아이디/비밀번호 찾기
                </Link>
              </div>
            </div>

            {/* 오른쪽 열: 버튼 */}
            <div className="w-full md:w-[180px] flex flex-col gap-5 pt-[40px]">
              <button
                type="submit"
                disabled={isLoading}
                className="w-full h-[64px] bg-[#9593D9] hover:bg-[#8381c9] text-white rounded-3xl text-lg font-bold shadow-lg transition-transform active:scale-95 disabled:opacity-70 disabled:cursor-not-allowed flex items-center justify-center"
              >
                {isLoading ? (
                  <Loader2 className="animate-spin w-6 h-6" />
                ) : (
                  "로그인"
                )}
              </button>

              {/* ✅ 조건부 렌더링: 부모 탭일 때만 회원가입 버튼 표시 */}
              {activeTab === "PARENT" && (
                <button
                  type="button"
                  onClick={() => navigate("/signup")}
                  className="w-full h-[64px] bg-[#E2E4EB] hover:bg-[#d1d5db] text-[#6B7280] rounded-3xl text-lg font-bold transition-colors mt-[20px]"
                >
                  회원가입
                </button>
              )}
            </div>
          </div>
        </form>
      </motion.div>
    </div>
  );
};

const TabButton = ({
  label,
  isActive,
  onClick,
}: {
  label: string;
  isActive: boolean;
  onClick: () => void;
}) => (
  <button
    type="button"
    onClick={onClick}
    className={cn(
      "w-[120px] py-3 rounded-2xl text-lg font-bold transition-all duration-300",
      isActive
        ? "bg-[#9593D9] text-white shadow-md"
        : "bg-[#F3F4F6] text-slate-400 hover:bg-slate-200"
    )}
  >
    {label}
  </button>
);

export default LoginPage;