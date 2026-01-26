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

  // React Hook Form 설정
  const {
    register,
    handleSubmit,
    
  } = useForm<LoginFormInputs>();

  const onSubmit = async (data: LoginFormInputs) => {
    setIsLoading(true);
    // API 연동 전 테스트용 로그
    console.log("로그인 시도:", { type: activeTab, ...data });

    // 1.5초 후 로그인 성공 처리 (Mock)
    setTimeout(() => {
      setIsLoading(false);

      // 탭에 따라 페이지 이동 분기
      if (activeTab === "PARENT") navigate("/parent/home");
      else if (activeTab === "DOCTOR") navigate("/doctor/dashboard");
      else navigate("/reception/dashboard");
    }, 1500);
  };

  return (
    // 배경 컨테이너: Flex-col로 설정
    <div className="min-h-screen w-full flex flex-col p-8 md:p-12 bg-[#E3E0F5] relative overflow-hidden">
      {/* --- Logo Area (Top Center) --- */}
      {/* self-center: 중앙 정렬, mb-auto: 아래 요소(카드)를 바닥으로 밀어냄 */}
      <div className="z-10 self-center mb-auto mt-4 md:mt-8">
        <div className="flex flex-col items-center gap-4">
          <div className="w-20 h-20 bg-[#D9D9D9] rounded-3xl shadow-sm" />
          <h1 className="text-6xl font-bold text-black font-['DM_Sans'] tracking-tight">
            AiTime
          </h1>
        </div>
      </div>

      {/* --- Main Card (Bottom Right) --- */}
      <motion.div
        initial={{ opacity: 0, y: 40, x: 20 }}
        animate={{ opacity: 1, y: 0, x: 0 }}
        transition={{ duration: 0.6, ease: "easeOut" }}
        // self-end: 우측 정렬
        className="w-full max-w-[760px] self-end bg-white rounded-[50px] shadow-[0px_10px_40px_rgba(149,147,217,0.4)] p-10 z-20"
      >
        <form onSubmit={handleSubmit(onSubmit)} className="w-full">
          {/* 1. 탭 영역 (우측 상단 정렬) */}
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

          {/* 2. 입력 & 버튼 그리드 (좌우 배치) */}
          <div className="flex flex-col md:flex-row gap-6 md:gap-8">
            {/* 왼쪽 열: 입력 필드 */}
            <div className="flex-1 space-y-5">
              {/* 아이디 */}
              <div className="space-y-2">
                <label className="block text-lg font-bold text-black ml-1">
                  아이디
                </label>
                <input
                  {...register("loginId", { required: true })} // required는 유지하되 메시지는 제거 가능
                  type="text"
                  placeholder="아이디를 입력하세요"
                  className={cn(
                    "w-full h-[64px] bg-gray-100 rounded-3xl px-6 text-lg border-2 border-transparent focus:border-[#9593D9] focus:bg-white transition-all outline-none placeholder:text-gray-400",
                    // border-red-400 제거됨 (에러 시에도 스타일 유지)
                  )}
                />
              </div>

              {/* 비밀번호 */}
              <div className="space-y-2">
                <label className="block text-lg font-bold text-black ml-1">
                  비밀번호
                </label>
                <input
                  {...register("password", { required: true })}
                  type="password"
                  placeholder="비밀번호를 입력하세요"
                  className={cn(
                    "w-full h-[64px] bg-gray-100 rounded-3xl px-6 text-lg border-2 border-transparent focus:border-[#9593D9] focus:bg-white transition-all outline-none placeholder:text-gray-400",
                    // border-red-400 제거됨
                  )}
                />
              </div>

              {/* 찾기 링크 */}
              <div className="flex justify-end pt-1">
                <Link
                  to="/find-account"
                  className="text-[#9593D9] text-sm font-bold hover:text-[#7a78b8] transition-colors"
                >
                  아이디/비밀번호 찾기
                </Link>
              </div>
            </div>

            {/* 오른쪽 열: 버튼 (높이 정렬을 위해 상단 패딩 추가) */}
            <div className="w-full md:w-[180px] flex flex-col gap-5 pt-[40px]">
              {/* 로그인 버튼 */}
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

              {/* 회원가입 버튼 */}
              <button
                type="button"
                onClick={() => navigate("/signup")}
                className="w-full h-[64px] bg-[#E2E4EB] hover:bg-[#d1d5db] text-[#6B7280] rounded-3xl text-lg font-bold transition-colors mt-[20px]"
              >
                회원가입
              </button>
            </div>
          </div>
        </form>
      </motion.div>
    </div>
  );
};

// ---------------------------
// 3. 서브 컴포넌트 (탭 버튼)
// ---------------------------
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
        : "bg-[#F3F4F6] text-slate-400 hover:bg-slate-200",
    )}
  >
    {label}
  </button>
);

export default LoginPage;
