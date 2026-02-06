// src/features/auth/pages/StaffLoginPage.tsx
// 병원 직원 로그인 페이지 - 데스크 테마 적용 (Formal Design)
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
import doctorLogo from "@/assets/doctorLogo.svg";

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
        <div className="min-h-screen w-full flex bg-[#F0F1F5] font-['Pretendard',sans-serif]">
            {/* 왼쪽 패널 - 브랜딩 (더 짙고 전문적인 컬러) */}
            <div className="hidden lg:flex lg:w-1/2 bg-gradient-to-br from-[#4A45B6] to-[#5A55D6] flex-col justify-center items-center p-12 relative overflow-hidden">
                {/* 배경 장식 (패턴 변경) */}
                <div className="absolute top-0 left-0 w-full h-full opacity-10 bg-[radial-gradient(#ffffff_1px,transparent_1px)] [background-size:20px_20px]" />
                <div className="absolute top-20 left-20 w-64 h-64 bg-white/5 rounded-full blur-3xl" />
                <div className="absolute bottom-20 right-20 w-80 h-80 bg-white/5 rounded-full blur-3xl" />

                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.6 }}
                    className="relative z-10 text-center text-white"
                >
                    <div className="mb-8 relative z-11">
                        <img
                            src={doctorLogo}
                            alt="AiTime Hospital Logo"
                            className="w-20 h-20 mx-auto"
                        />
                    </div>
                    <h1 className="text-3xl font-bold mb-3 font-['DM_Sans'] tracking-tight">AiTime Hospital</h1>
                    <p className="text-white/80 text-lg font-light">병원 전용 통합 관리 시스템</p>
                    <div className="mt-8 flex gap-2 justify-center opacity-60 text-xs">
                        <span>Secure Access</span>
                        <span>•</span>
                        <span>Authorized Personnel Only</span>
                    </div>
                </motion.div>
            </div>

            {/* 오른쪽 패널 - 로그인 폼 */}
            <div className="flex-1 flex flex-col justify-center items-center p-8 lg:p-12">
                <motion.div
                    initial={{ opacity: 0, x: 20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ duration: 0.5 }}
                    className="w-full max-w-[400px] bg-white rounded-none shadow-xl shadow-gray-200/50 p-10 border border-gray-100"
                >
                    {/* 모바일용 로고 */}
                    <div className="lg:hidden text-center mb-8">
                        <img
                            src={doctorLogo}
                            alt="AiTime Hospital Logo"
                            className="w-12 h-12 mx-auto mb-3"
                        />
                        <h1 className="text-xl font-bold text-[#1A1A1A] font-['DM_Sans']">AiTime Hospital</h1>
                    </div>

                    {/* 타이틀 */}
                    <div className="mb-8 hidden lg:block">
                        <h2 className="text-2xl font-bold text-[#1A1A1A] mb-2">Staff Login</h2>
                        <p className="text-gray-500 text-sm">할당된 병원 계정으로 접속해주세요.</p>
                    </div>

                    {/* 탭 선택 (더 각지고 깔끔하게) */}
                    <div className="bg-[#F3F4F6] p-1 rounded-none flex gap-1 mb-8">
                        <button
                            type="button"
                            onClick={() => setActiveTab("DOCTOR")}
                            className={cn(
                                "flex-1 py-2.5 rounded-none text-sm font-semibold transition-all duration-200",
                                activeTab === "DOCTOR"
                                    ? "bg-white text-[#5A55D6] shadow-sm ring-1 ring-black/5"
                                    : "text-gray-500 hover:text-gray-700"
                            )}
                        >
                            의료진
                        </button>
                        <button
                            type="button"
                            onClick={() => setActiveTab("DESK")}
                            className={cn(
                                "flex-1 py-2.5 rounded-none text-sm font-semibold transition-all duration-200",
                                activeTab === "DESK"
                                    ? "bg-white text-[#5A55D6] shadow-sm ring-1 ring-black/5"
                                    : "text-gray-500 hover:text-gray-700"
                            )}
                        >
                            접수처
                        </button>
                    </div>

                    {/* 로그인 폼 */}
                    <form onSubmit={handleSubmit(handleLogin)} className="space-y-5">
                        {/* 아이디 입력 */}
                        <div className="space-y-1.5">
                            <label className="text-xs font-semibold text-gray-700 ml-1">아이디</label>
                            <div className="relative">
                                <div className="absolute left-3.5 top-1/2 -translate-y-1/2 text-gray-400">
                                    <User className="w-4 h-4" />
                                </div>
                                <input
                                    type="text"
                                    {...register("loginId", { required: true })}
                                    autoCapitalize="off"
                                    autoComplete="username"
                                    autoCorrect="off"
                                    className="w-full h-11 pl-10 pr-4 bg-gray-50 border border-gray-200 rounded-none text-sm outline-none focus:bg-white focus:border-[#5A55D6] focus:ring-1 focus:ring-[#5A55D6] transition-all"
                                    placeholder="Enter your ID"
                                />
                            </div>
                        </div>

                        {/* 비밀번호 입력 */}
                        <div className="space-y-1.5">
                            <label className="text-xs font-semibold text-gray-700 ml-1">비밀번호</label>
                            <div className="relative">
                                <div className="absolute left-3.5 top-1/2 -translate-y-1/2 text-gray-400">
                                    <Lock className="w-4 h-4" />
                                </div>
                                <input
                                    type="password"
                                    {...register("password", { required: true })}
                                    className="w-full h-11 pl-10 pr-4 bg-gray-50 border border-gray-200 rounded-none text-sm outline-none focus:bg-white focus:border-[#5A55D6] focus:ring-1 focus:ring-[#5A55D6] transition-all"
                                    placeholder="Enter your password"
                                />
                            </div>
                        </div>

                        {/* 로그인 버튼 */}
                        <Button
                            type="submit"
                            disabled={isLoading}
                            className="w-full h-11 bg-[#5A55D6] hover:bg-[#4A45B6] text-white font-bold rounded-none transition-all shadow-md shadow-[#5A55D6]/20 mt-2 disabled:opacity-50"
                        >
                            {isLoading ? "Signing in..." : "Sign In"}
                        </Button>
                    </form>

                    {/* 구분선 */}
                    <div className="relative my-8">
                        <div className="absolute inset-0 flex items-center">
                            <div className="w-full border-t border-gray-200" />
                        </div>
                        <div className="relative flex justify-center">
                            <span className="px-4 bg-white text-xs text-gray-400 uppercase tracking-wider">Or</span>
                        </div>
                    </div>

                    {/* 부모 로그인 링크 */}
                    <div className="text-center">
                        <button
                            type="button"
                            onClick={() => navigate("/")}
                            className="text-sm text-gray-500 hover:text-[#5A55D6] transition-colors"
                        >
                            ← 부모 계정으로 돌아가기
                        </button>
                    </div>

                    {/* 푸터 */}
                    <div className="mt-8 pt-6 border-t border-gray-100 text-center">
                        <p className="text-[10px] text-gray-400">
                            © 2026 AiTime. All rights reserved.<br />
                            Unauthorized access is prohibited.
                        </p>
                    </div>
                </motion.div>
            </div>
        </div>
    );
}
