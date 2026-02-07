// src/features/auth/components/LoginForm.tsx
import type { UseFormReturn } from "react-hook-form"; // [수정] type 추가
import { Link, useNavigate } from "react-router-dom";
import { Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";
import type { AuthTabType, LoginCredentials } from "../types"; // [수정] type 추가

interface LoginFormProps {
  activeTab: AuthTabType;
  isLoading: boolean;
  formMethods: UseFormReturn<LoginCredentials>;
  onSubmit: (data: LoginCredentials) => void;
}

export default function LoginForm({
  activeTab,
  isLoading,
  formMethods,
  onSubmit,
}: LoginFormProps) {
  const navigate = useNavigate();
  const { register, handleSubmit } = formMethods;

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="w-full">
      {/* 입력 & 버튼 그리드 */}
      <div className="flex flex-col md:flex-row gap-6 md:gap-8">
        {/* 왼쪽 열: 입력 필드 */}
        <div className="flex-1 space-y-5">
          {/* 아이디 입력 */}
          <div className="space-y-2">
            <label className="block text-lg font-bold text-black ml-1">
              아이디
            </label>
            <input
              {...register("loginId", { required: true })}
              type="text"
              placeholder="아이디를 입력하세요"
              autoCapitalize="off"
              autoComplete="username"
              autoCorrect="off"
              className={cn(
                "w-full h-[64px] bg-gray-100 rounded-3xl px-6 text-lg border-2 border-transparent focus:border-[#9593D9] focus:bg-white transition-all outline-none placeholder:text-gray-400",
              )}
            />
          </div>

          {/* 비밀번호 입력 */}
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

        {/* 오른쪽 열: 버튼 */}
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

          {/* 회원가입 버튼 (부모 탭일 때만) */}
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
  );
}
