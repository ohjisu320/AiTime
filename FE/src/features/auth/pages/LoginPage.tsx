// src/features/auth/pages/LoginPage.tsx
import { motion } from "framer-motion";
import { useLoginPage } from "../hooks/useLoginPage";
import LoginTabs from "../components/LoginTabs";
import LoginForm from "../components/LoginForm";

export default function LoginPage() {
  // Hook에서 로직 가져오기
  const { activeTab, setActiveTab, isLoading, formMethods, handleLogin } =
    useLoginPage();

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
        {/* 1. 탭 컴포넌트 */}
        <LoginTabs activeTab={activeTab} onTabChange={setActiveTab} />

        {/* 구분선 */}
        <div className="w-full h-[1px] bg-slate-200 mb-8" />

        {/* 2. 폼 컴포넌트 */}
        <LoginForm
          activeTab={activeTab}
          isLoading={isLoading}
          formMethods={formMethods}
          onSubmit={handleLogin}
        />
      </motion.div>
    </div>
  );
}
