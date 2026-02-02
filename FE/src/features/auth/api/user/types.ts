// src/features/auth/api/user/types.ts

// 내 정보 조회 응답 (GET /user/me)
export interface UserInfoResponse {
  userId: string;
  name: string;
  phoneNumber: string;
  loginId: string;
  // 필요한 경우 추가 필드 정의
}

// 내 정보 수정 요청 (PATCH /user/me)
export interface UserUpdateRequest {
  name: string;
  phoneNumber: string;
}
