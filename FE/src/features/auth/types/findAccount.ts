// src/features/auth/types/findAccount.ts

export type FindTabType = "FIND_ID" | "RESET_PW";

// API: /auth/phone/verification (요청)
export interface PhoneVerificationRequest {
  phoneNumber: string;
}

// API: /auth/phone/verify (요청)
export interface PhoneVerifyRequest {
  phoneNumber: string;
  verificationCode: string;
}

// API: /user/password (비밀번호 변경 요청)
export interface PasswordChangeRequest {
  userId: string; // PhoneVerifyForPasswordData에서 획득
  password: string;
  confirmPassword: string; // UI용 필드
}

// 아이디 찾기 결과 데이터
export interface FindIdResult {
  loginId: string;
  createdAt: string;
}
