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

  // 로그인 핸들러
  const handleLogin = async (data: LoginCredentials) => {
    setIsLoading(true);

    try {
      // API 엔드포인트 결정
      const endpoint = activeTab === "PARENT"
        ? "/user/login"
        : "/hospital-staff/login";

      console.log(`[${activeTab}] 로그인 요청:`, { loginId: data.loginId });

      // 실제 API 호출 (axios 사용)
      const axios = (await import('axios')).default;
      const response = await axios.post(
        `${import.meta.env.VITE_API_BASE_URL}${endpoint}`,
        {
          loginId: data.loginId,
          password: data.password,
        }
      );

      console.log('로그인 응답:', response.data);

      // ✅ 성공 체크 (code 200)
      if (response.data.code === 200) {
        // 백엔드 응답 구조: { code, status, message, data: { accessToken, refreshToken, user } }
        const payload = response.data.data;
        const { accessToken, refreshToken } = payload;

        if (!accessToken) {
          throw new Error('토큰이 없습니다.');
        }

        // ✅ localStorage에 토큰 저장
        localStorage.setItem('accessToken', accessToken);
        if (refreshToken) {
          localStorage.setItem('refreshToken', refreshToken);
        }

        // ✅ 사용자 정보도 저장 (있는 경우)
        if (payload.user) {
          // userId를 id로도 매핑 (기존 컴포넌트 호환성)
          const userData = {
            ...payload.user,
            id: payload.user.userId || payload.user.id,
          };
          localStorage.setItem('user', JSON.stringify(userData));
          console.log('✅ 사용자 정보 저장:', userData);
        }

        console.log('✅ 로그인 성공! 토큰 저장 완료');

        // 탭에 따른 페이지 이동
        switch (activeTab) {
          case "PARENT":
            navigate("/auth/profile-select");
            break;
          case "DOCTOR":
            navigate("/doctor/dashboard");
            break;
          case "DESK":
            navigate("/reception/dashboard");
            break;
        }
      } else {
        // API는 성공했지만 비즈니스 로직 실패
        const errorMessage = response.data.message || '로그인에 실패했습니다.';
        alert(errorMessage);
      }

    } catch (error: any) {
      console.error('❌ 로그인 에러:', error);

      // 에러 메시지 표시
      const errorMessage = error?.response?.data?.message || error.message || "로그인 중 오류가 발생했습니다.";
      alert(errorMessage); // TODO: toast로 교체

    } finally {
      setIsLoading(false);
    }
  };

  return {
    activeTab,
    setActiveTab,
    isLoading,
    formMethods,
    handleLogin,
  };
};
