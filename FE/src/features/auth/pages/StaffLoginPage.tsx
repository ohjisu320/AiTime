// src/features/auth/pages/StaffLoginPage.tsx
// 병원 직원 로그인 페이지 - 부모 로그인 스타일과 통일
import { useState } from "react";
import { useForm } from "react-hook-form";
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { User, Lock } from "lucide-react";
import api from "@/api/axiosConfig";
import type { ApiResponseHospitalStaffLogin } from "@/api/types/auth.types";
import { StaffRole } from "@/api/types";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import parentLogo from "@/assets/parentLogo.svg";

type StaffTab = "DOCTOR" | "DESK";

interface LoginCredentials {
    loginId: string;
    password: string;
}

export default function StaffLoginPage() {
    const navigate = useNavigate();
    const [activeTab, setActiveTab] = useState<StaffTab>("DOCTOR");
    const [isLoading, setIsLoading] = useState(false);
    const { register, handleSubmit } = useForm<LoginCredentials>();

    const handleLogin = async (data: LoginCredentials) => {
        setIsLoading(true);

        try {
            console.log(`[${activeTab}] 병원 직원 로그인 요청:`, { loginId: data.loginId });

            const response = await api.post<ApiResponseHospitalStaffLogin>('/hospital-staff/login', {
                loginId: data.loginId,
                password: data.password,
            });

            if (response.data.code === 200) {
                const { accessToken, refreshToken, hospitalStaffInfoDTO } = response.data.data;

                localStorage.setItem('accessToken', accessToken);
                if (refreshToken) {
                    localStorage.setItem('refreshToken', refreshToken);
                }

                const userData = {
                    id: hospitalStaffInfoDTO.hospitalStaffId,
                    name: hospitalStaffInfoDTO.name,
                    staffRole: hospitalStaffInfoDTO.staffRole,
                    type: 'STAFF'
                };
                localStorage.setItem('user', JSON.stringify(userData));

                let redirectUrl = "/";
                if (hospitalStaffInfoDTO.staffRole === StaffRole.DOCTOR) {
                    redirectUrl = "/doctor/dashboard";
                } else if (hospitalStaffInfoDTO.staffRole === StaffRole.DESK) {
                    redirectUrl = "/reception/dashboard";
                }

                console.log('✅ 로그인 성공! 리다이렉트:', redirectUrl);
                navigate(redirectUrl);
            } else {
                throw new Error(response.data.message);
            }
        } catch (error: any) {
            console.error('❌ 로그인 에러:', error);
            const errorMessage = error?.response?.data?.message || error.message || "로그인 중 오류가 발생했습니다.";
            alert(errorMessage);
        } finally {
            setIsLoading(false);
        }
    };

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
                    <p className="text-white/80 text-lg">병원 직원 전용 시스템</p>
                    <p className="text-white/60 text-sm mt-2">ASD 조기 진단 지원 플랫폼</p>
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
                        <p className="text-gray-500 text-sm">병원 직원 전용</p>
                    </div>

                    {/* 타이틀 */}
                    <div className="mb-6 hidden lg:block">
                        <h2 className="text-2xl font-bold text-[#1A1A1A] mb-2">로그인</h2>
                        <p className="text-gray-500">병원 직원 계정으로 로그인하세요</p>
                    </div>

                    {/* 탭 선택 */}
                    <div className="bg-[#F3F4F6] p-1 rounded-2xl flex gap-1 mb-6">
                        <button
                            type="button"
                            onClick={() => setActiveTab("DOCTOR")}
                            className={cn(
                                "flex-1 py-3 rounded-xl text-sm font-bold transition-all duration-200",
                                activeTab === "DOCTOR"
                                    ? "bg-[#9593D9] text-white shadow-md"
                                    : "text-gray-400 hover:text-gray-600"
                            )}
                        >
                            의료진
                        </button>
                        <button
                            type="button"
                            onClick={() => setActiveTab("DESK")}
                            className={cn(
                                "flex-1 py-3 rounded-xl text-sm font-bold transition-all duration-200",
                                activeTab === "DESK"
                                    ? "bg-[#9593D9] text-white shadow-md"
                                    : "text-gray-400 hover:text-gray-600"
                            )}
                        >
                            접수처
                        </button>
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

                    {/* 구분선 */}
                    <div className="relative my-6">
                        <div className="absolute inset-0 flex items-center">
                            <div className="w-full border-t border-slate-200" />
                        </div>
                        <div className="relative flex justify-center">
                            <span className="px-4 bg-white text-sm text-gray-400">또는</span>
                        </div>
                    </div>

                    {/* 부모 로그인 링크 */}
                    <button
                        type="button"
                        onClick={() => navigate("/")}
                        className="w-full h-12 border border-gray-200 rounded-xl text-sm text-gray-600 font-medium hover:bg-gray-50 transition-all"
                    >
                        부모 계정으로 로그인 →
                    </button>

                    {/* 안내 문구 */}
                    <p className="text-center text-xs text-gray-400 mt-6">
                        {activeTab === "DOCTOR" ? "의료진" : "접수처"} 계정으로 로그인합니다.
                        <br />
                        계정 문의는 병원 관리자에게 연락하세요.
                    </p>
                </motion.div>
            </div>
        </div>
    );
}
