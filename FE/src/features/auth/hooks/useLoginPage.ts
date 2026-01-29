// src/features/auth/hooks/useLoginPage.ts
import { useState } from "react";
import { useForm } from "react-hook-form";
import { useNavigate } from "react-router-dom";
import type { AuthTabType, LoginCredentials } from "../types"; // [수정] type 추가

export const useLoginPage = () => {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState<AuthTabType>("PARENT");
  const [isLoading, setIsLoading] = useState(false);

  // react-hook-form 설정
  const formMethods = useForm<LoginCredentials>();

  // 로그인 핸들러 (Mock Logic)
  const handleLogin = async (data: LoginCredentials) => {
    setIsLoading(true);

    // [API 명세 준수 체크]
    // 1. 부모 로그인: POST /api/v1/user/login -> Body: { loginId, password }
    // 2. 의료진/데스크: POST /api/v1/hospital-staff/login -> Body: { loginId, password }
    console.log(`[${activeTab}] 로그인 요청:`, data);

    // Mock: 1.5초 후 성공 처리
    setTimeout(() => {
      setIsLoading(false);

      // 탭에 따른 페이지 이동
      switch (activeTab) {
        case "PARENT":
          navigate("/parent/select-profile");
          break;
        case "DOCTOR":
          navigate("/doctor/dashboard");
          break;
        case "DESK":
          navigate("/reception/dashboard");
          break;
      }
    }, 1500);
  };

  return {
    activeTab,
    setActiveTab,
    isLoading,
    formMethods,
    handleLogin,
  };
};
