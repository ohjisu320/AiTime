// src/features/auth/api/user/userApi.ts
import api from "@/api/axiosConfig";
import type { ApiResponse } from "@/features/auth/api/child/types"; // 공통 응답 타입 재사용
import type { UserInfoResponse, UserUpdateRequest } from "./types";

/**
 * 1. 내 정보 조회
 * GET /user/me
 */
export const getMyInfo = async (): Promise<UserInfoResponse> => {
  console.log("🚀 [GET] Fetching My Info...");
  const response = await api.get<ApiResponse<UserInfoResponse>>("/user/me");
  console.log("✅ My Info Success:", response.data.data);
  return response.data.data;
};

/**
 * 2. 내 정보 수정
 * PATCH /user/me
 */
export const updateMyInfo = async (data: UserUpdateRequest): Promise<void> => {
  console.log("🚀 [PATCH] Updating My Info:", data);
  await api.patch<ApiResponse<null>>("/user/me", data);
  console.log("✅ Update Success");
};

/**
 * 3. 회원 탈퇴
 * DELETE /user
 */
export const withdrawUser = async (): Promise<void> => {
  console.log("🚀 [DELETE] Withdrawing User...");
  await api.delete<ApiResponse<null>>("/user");
  console.log("✅ Withdraw Success");
};
