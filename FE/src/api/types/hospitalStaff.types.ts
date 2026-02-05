import type { ApiResponse } from '../types';

// =================================================================
// Hospital Staff Auth (병원 관계자 인증)
// =================================================================

export interface HospitalStaffLoginRequest {
    id: string;      // "root" 등
    password: string; // "1234" 등
}

export interface HospitalStaffLoginResponseData {
    accessToken: string;
    refreshToken: string; // 쿠키로 오지만 응답 바디에도 포함될 수 있음 (Swagger에는 *.*로 되어있어 구체적 필드 확인 필요, 일단 토큰류 가정)
    // 필요 시 수정: Swagger의 ApiResponseHospitalStaffLoginResponse 구조를 정확히 모르면 any로 두거나 추후 수정
    // 보통 { accessToken: string, ... }
}

export type ApiResponseHospitalStaffLoginResponse = ApiResponse<HospitalStaffLoginResponseData>;

export interface HospitalStaffProfileResponse {
    staffId: string;
    name: string;
    role: string; // "DOCTOR", "NURSE", "ADMIN" etc
    hospitalName: string;
}

export type ApiResponseHospitalStaffProfile = ApiResponse<HospitalStaffProfileResponse>;
