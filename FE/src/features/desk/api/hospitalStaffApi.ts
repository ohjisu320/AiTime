import api from "@/api/axiosConfig";
import type { ApiResponse } from "@/api/types";

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
