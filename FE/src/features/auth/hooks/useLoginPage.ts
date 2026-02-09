import { useState } from "react";
import { useForm } from "react-hook-form";
import { useNavigate } from "react-router-dom";
import api from '@/api/axiosConfig';
import type { ApiResponseUserLogin } from '@/api/types/auth.types';

type AuthTabType = "PARENT";

interface LoginCredentials {
  loginId: string;
  password: string;
}

export const useLoginPage = () => {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState<AuthTabType>("PARENT");
  const [isLoading, setIsLoading] = useState(false);

  // react-hook-form 설정
  const formMethods = useForm<LoginCredentials>();

  // 로그인 핸들러 (부모 전용)
  const handleLogin = async (data: LoginCredentials) => {
    setIsLoading(true);

    try {
      console.log(`[PARENT] 로그인 요청:`, { loginId: data.loginId });

      // 부모(일반 사용자) 로그인
      const response = await api.post<ApiResponseUserLogin>('/user/login', {
        loginId: data.loginId,
        password: data.password,
      });

      if (response.data.code === 200) {
        const { accessToken, refreshToken, userInfoDTO } = response.data.data;

        // 토큰 저장
        localStorage.setItem('accessToken', accessToken);
        if (refreshToken) {
          localStorage.setItem('refreshToken', refreshToken);
        }

        // 사용자 정보 저장
        const userData = {
          id: userInfoDTO.userId,
          name: userInfoDTO.name,
          userRole: userInfoDTO.userRole,
          type: 'PARENT'
        };
        localStorage.setItem('user', JSON.stringify(userData));

        console.log('✅ 로그인 성공! 리다이렉트: /parent/select-profile');
        navigate("/parent/select-profile");
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

  return {
    activeTab,
    setActiveTab,
    isLoading,
    formMethods,
    handleLogin,
  };
};
