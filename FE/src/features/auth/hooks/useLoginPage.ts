import { useState } from "react";
import { useForm } from "react-hook-form";
import { useNavigate } from "react-router-dom";
import type { AuthTabType, LoginCredentials } from "../types";
import api from '@/api/axiosConfig';
import type { ApiResponseUserLogin, ApiResponseHospitalStaffLogin } from '@/api/types/auth.types';
import { StaffRole } from '@/api/types';

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
      console.log(`[${activeTab}] 로그인 요청:`, { loginId: data.loginId });

      let redirectUrl = "";

      if (activeTab === "PARENT") {
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

          redirectUrl = "/parent/select-profile"; // 오타 수정: path -> parent
        } else {
          throw new Error(response.data.message);
        }

      } else {
        // 병원 관계자 로그인
        const response = await api.post<ApiResponseHospitalStaffLogin>('/hospital-staff/login', {
          loginId: data.loginId,
          password: data.password,
        });

        if (response.data.code === 200) {
          const { accessToken, refreshToken, hospitalStaffInfoDTO } = response.data.data;

          // 토큰 저장
          localStorage.setItem('accessToken', accessToken);
          if (refreshToken) {
            localStorage.setItem('refreshToken', refreshToken);
          }

          // 직원 정보 저장
          const userData = {
            id: hospitalStaffInfoDTO.hospitalStaffId,
            name: hospitalStaffInfoDTO.name,
            staffRole: hospitalStaffInfoDTO.staffRole,
            type: 'STAFF'
          };
          localStorage.setItem('user', JSON.stringify(userData));

          // 역할에 따른 라우팅
          if (hospitalStaffInfoDTO.staffRole === StaffRole.DOCTOR) {
            redirectUrl = "/doctor/dashboard";
          } else if (hospitalStaffInfoDTO.staffRole === StaffRole.DESK) {
            redirectUrl = "/reception/dashboard";
          } else {
            redirectUrl = "/"; // Fallback
          }
        } else {
          throw new Error(response.data.message);
        }
      }

      console.log('✅ 로그인 성공! 리다이렉트:', redirectUrl);
      navigate(redirectUrl);

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
