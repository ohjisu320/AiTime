// src/features/auth/types/signup.ts

// ✅ API 명세서: UserJoinRequest 구조 준수
export interface UserJoinRequest {
  loginId: string;
  password: string;
  name: string;
  phoneNumber: string;
  privacyAgreed: boolean;
}

// UI용 폼 데이터 (비밀번호 확인, 인증코드 등 UI 전용 필드 포함)
export interface SignupFormData {
  loginId: string; // API: loginId
  password: string; // API: password
  confirmPassword: string;
  name: string; // API: name
  phoneNumber: string; // API: phoneNumber
  authCode: string;
}

// 약관 동의 상태
export interface TermsAgreement {
  term1: boolean; // 필수 약관
  term2: boolean; // 개인정보 수집
}
