import api from "@/api/axiosConfig";
import type { ApiResponse } from "@/api/types";
import type { HospitalStaffLoginRequest, ApiResponseHospitalStaffLoginResponse } from "@/api/types/hospitalStaff.types";

export interface DoctorResponse {
    doctorId: string;
    doctorName: string;
}

export type ApiResponseDoctorList = ApiResponse<DoctorResponse[]>;

/**
 * 의사 목록 조회
 * GET /hospital-staff/doctors
 */
export const getDoctors = async () => {
    const response = await api.get<ApiResponseDoctorList>('/hospital-staff/doctors');
    return response.data;
};

/**
 * 병원 관계자 로그인
 * POST /hospital-staff/login
 */
export const loginHospitalStaff = async (data: HospitalStaffLoginRequest) => {
    console.log(`📡 [API] 병원 관계자 로그인 요청`);
    const response = await api.post<ApiResponseHospitalStaffLoginResponse>(
        '/hospital-staff/login',
        data
    );
    return response.data;
};

/**
 * 병원 관계자 로그아웃
 * POST /hospital-staff/logout
 */
export const logoutHospitalStaff = async () => {
    console.log(`📡 [API] 병원 관계자 로그아웃 요청`);
    // refreshToken은 쿠키로 자동 전송된다고 가정
    const response = await api.post<ApiResponse<any>>(
        '/hospital-staff/logout'
    );
    return response.data;
};

/**
 * 토큰 갱신
 * POST /hospital-staff/refresh
 */
/**
 * 토큰 갱신
 * POST /hospital-staff/refresh
 */
export const refreshHospitalStaffToken = async () => {
    console.log(`📡 [API] 병원 관계자 토큰 갱신 요청`);
    // refreshToken은 쿠키로 자동 전송된다고 가정
    const response = await api.post<ApiResponseHospitalStaffLoginResponse>(
        '/hospital-staff/refresh'
    );
    return response.data;
};

import type { ApiResponseHospitalStaffProfile } from "@/api/types/hospitalStaff.types";

/**
 * 로그인한 병원 관계자 정보 조회
 * GET /hospital-staff/profile (임의 지정, 실제 API 명세 확인 필요)
 */
export const getHospitalStaffProfile = async () => {
    // TODO: 실제 API 엔드포인트 확인 필요 (/me, /profile 등)
    const response = await api.get<ApiResponseHospitalStaffProfile>('/hospital-staff/profile');
    return response.data;
};
