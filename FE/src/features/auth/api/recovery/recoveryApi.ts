// src/features/auth/api/recovery/recoveryApi.ts
import api from "@/api/axiosConfig";

// 공통 응답 타입
interface ApiResponse<T> {
  code: number;
  status: string;
  message: string;
  data: T;
}

// 1. 아이디 찾기 응답 데이터
export interface FindIdResponse {
  loginId: string;
  createdAt: string; // ISO DateTime
}

// 2. 본인 확인(비밀번호 찾기용) 응답 데이터
export interface VerifyIdentityResponse {
  isVerified: boolean;
  userId: string; // 비밀번호 변경 시 식별자로 사용
}

// =================================================================
// API Functions
// =================================================================

/**
 * 1. 아이디 찾기
 * GET /user/get-id?phoneNumber=...
 */
export const findLoginId = async (
  phoneNumber: string,
): Promise<FindIdResponse> => {
  console.log(`🚀 [GET] Find ID for: ${phoneNumber}`);
  const response = await api.get<ApiResponse<FindIdResponse>>(`/user/get-id`, {
    params: { phoneNumber },
  });
  return response.data.data;
};

/**
 * 2. 본인 확인 (비밀번호 재설정 전 단계)
 * GET /user/verify-identity?phoneNumber=...
 */
export const verifyIdentity = async (
  phoneNumber: string,
): Promise<VerifyIdentityResponse> => {
  console.log(`🚀 [GET] Verify Identity for: ${phoneNumber}`);
  const response = await api.get<ApiResponse<VerifyIdentityResponse>>(
    `/user/verify-identity`,
    { params: { phoneNumber } },
  );
  return response.data.data;
};

/**
 * 3. 비밀번호 재설정
 * PATCH /user/password
 */
export const resetPassword = async (
  userId: string,
  password: string,
): Promise<void> => {
  console.log(`🚀 [PATCH] Reset Password for userId: ${userId}`);
  await api.patch<ApiResponse<null>>("/user/password", {
    userId,
    password,
  });
};
