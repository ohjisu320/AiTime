// src/features/auth/pages/LoginPage.tsx
import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { User, Lock } from "lucide-react";
import { Button } from "@/components/ui/button";
import parentLogo from '@/assets/parentLogo.svg';
import { useLoginPage } from "../hooks/useLoginPage";

export default function LoginPage() {
  const { isLoading, formMethods, handleLogin } = useLoginPage();
  const { register, handleSubmit } = formMethods;

  return (
    <div className="min-h-screen w-full flex bg-[#E3E0F5] font-['Pretendard',sans-serif]">
      {/* 왼쪽 패널 - 브랜딩 */}
      <div className="hidden lg:flex lg:w-1/2 bg-gradient-to-br from-[#9593D9] to-[#B8B6E8] flex-col justify-center items-center p-12 relative overflow-hidden">
        {/* 배경 장식 */}
        <div className="absolute top-20 left-20 w-64 h-64 bg-white/10 rounded-full blur-3xl" />
        <div className="absolute bottom-20 right-20 w-80 h-80 bg-white/10 rounded-full blur-3xl" />

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="relative z-10 text-center"
        >
          <img
            src={parentLogo}
            alt="AiTime Logo"
            className="w-24 h-24 mx-auto mb-6"
          />
          <h1 className="text-4xl font-bold text-white mb-3 font-['DM_Sans']">AiTime</h1>
          <p className="text-white/80 text-lg">우리 아이 발달 관리의 시작</p>
          <p className="text-white/60 text-sm mt-2">부모 전용 서비스</p>
        </motion.div>
      </div>

      {/* 오른쪽 패널 - 로그인 폼 */}
      <div className="flex-1 flex flex-col justify-center items-center p-8 lg:p-12">
        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.5 }}
          className="w-full max-w-[420px] bg-white rounded-[40px] shadow-[0px_10px_40px_rgba(149,147,217,0.3)] p-10"
        >
          {/* 모바일용 로고 */}
          <div className="lg:hidden text-center mb-6">
            <img
              src={parentLogo}
              alt="AiTime Logo"
              className="w-16 h-16 mx-auto mb-3"
            />
            <h1 className="text-2xl font-bold text-black font-['DM_Sans']">AiTime</h1>
            <p className="text-gray-500 text-sm">부모 전용 서비스</p>
          </div>

          {/* 타이틀 */}
          <div className="mb-6 hidden lg:block">
            <h2 className="text-2xl font-bold text-[#1A1A1A] mb-2">로그인</h2>
            <p className="text-gray-500">계정으로 로그인하여 시작하세요</p>
          </div>

          {/* 로그인 폼 */}
          <form onSubmit={handleSubmit(handleLogin)} className="space-y-4">
            {/* 아이디 입력 */}
            <div className="relative">
              <div className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400">
                <User className="w-5 h-5" />
              </div>
              <input
                type="text"
                {...register("loginId", { required: true })}
                placeholder="아이디"
                className="w-full h-12 pl-12 pr-4 bg-white border border-gray-200 rounded-xl text-sm outline-none focus:border-[#9593D9] focus:ring-2 focus:ring-[#9593D9]/20 transition-all"
              />
            </div>

            {/* 비밀번호 입력 */}
            <div className="relative">
              <div className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400">
                <Lock className="w-5 h-5" />
              </div>
              <input
                type="password"
                {...register("password", { required: true })}
                placeholder="비밀번호"
                className="w-full h-12 pl-12 pr-4 bg-white border border-gray-200 rounded-xl text-sm outline-none focus:border-[#9593D9] focus:ring-2 focus:ring-[#9593D9]/20 transition-all"
              />
            </div>

            {/* 로그인 버튼 */}
            <Button
              type="submit"
              disabled={isLoading}
              className="w-full h-12 bg-[#9593D9] hover:bg-[#7B78C5] text-white font-bold rounded-xl transition-all shadow-lg shadow-[#9593D9]/25 disabled:opacity-50"
            >
              {isLoading ? "로그인 중..." : "로그인"}
            </Button>
          </form>

          {/* 소셜 로그인 / 회원가입 링크 등 (필요 시 추가) */}
          {/* <div className="mt-4 text-center">
             <Link to="/signup" className="text-sm text-gray-400 hover:text-[#9593D9]">회원가입</Link>
          </div> */}

          {/* 구분선 */}
          <div className="relative my-6">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-slate-200" />
            </div>
            <div className="relative flex justify-center">
              <span className="px-4 bg-white text-sm text-gray-400">또는</span>
            </div>
          </div>

          {/* 직원 로그인 링크 */}
          <Link
            to="/staff-login"
            className="block w-full h-12 flex items-center justify-center border border-gray-200 rounded-xl text-sm text-gray-600 font-medium hover:bg-gray-50 transition-all text-center no-underline"
          >
            병원 직원 로그인 →
          </Link>

          {/* 안내 문구 */}
          <p className="text-center text-xs text-gray-400 mt-6">
            병원 방문 전 미리 아이의 발달 상태를<br />
            체크하고 관리할 수 있습니다.
          </p>
        </motion.div>
      </div>
    </div>
  );
}
