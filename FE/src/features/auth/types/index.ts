// src/features/auth/types/index.ts

// 탭 종류 (부모 / 의료진 / 접수처)
export type AuthTabType = "PARENT" | "DOCTOR" | "DESK";

// API 명세 준수: UserLoginRequest & StaffLoginRequest
// 두 요청 모두 loginId, password 필드를 가집니다.
export interface LoginCredentials {
  loginId: string;
  password: string;
}
