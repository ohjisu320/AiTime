// src/features/auth/api/signup/signupApi.ts
import api from "@/api/axiosConfig";
import type { UserJoinRequest } from "../../types/signup"; // 또는 "@/features/auth/types/signup"

// 공통 응답 타입
interface ApiResponse<T> {
  code: number;
  status: string;
  message: string;
  data: T;
}

/**
 * 1. 아이디 중복 확인
 * GET /user/duplicate-id?loginId=...
 */
export const checkDuplicateId = async (loginId: string): Promise<boolean> => {
  console.log(`🚀 [GET] Check Duplicate ID: ${loginId}`);
  const response = await api.get<ApiResponse<{ isDuplicate: boolean }>>(
    `/user/duplicate-id`,
    { params: { loginId } },
  );
  return response.data.data.isDuplicate;
};

/**
 * 2. 휴대폰 인증번호 발송
 * POST /auth/phone/verification
 */
export const sendPhoneVerification = async (phoneNumber: string) => {
  console.log(`🚀 [POST] Send Verification Code: ${phoneNumber}`);
  const response = await api.post<ApiResponse<{ expiredAt: string }>>(
    "/auth/phone/verification",
    { phoneNumber },
  );
  return response.data.data;
};

/**
 * 3. 휴대폰 인증번호 검증
 * POST /auth/phone/verify
 */
export const verifyPhoneCode = async (
  phoneNumber: string,
  verificationCode: string,
): Promise<boolean> => {
  console.log(`🚀 [POST] Verify Code: ${phoneNumber}, ${verificationCode}`);
  const response = await api.post<ApiResponse<{ [key: string]: boolean }>>(
    "/auth/phone/verify",
    { phoneNumber, verificationCode },
  );

  // 응답 데이터에서 boolean 값 추출 (예: {"01012345678": true})
  if (!response.data.data) return false;
  const values = Object.values(response.data.data);
  return values.length > 0 && values[0] === true;
};

/**
 * 4. 회원가입 요청
 * POST /user/join
 */
export const signupUser = async (data: UserJoinRequest) => {
  console.log("🚀 [POST] Join User:", data);
  const response = await api.post<ApiResponse<{ userId: string }>>(
    "/user/join",
    data,
  );
  return response.data.data;
};
