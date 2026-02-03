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

import type { ApiResponseListReservationListResponse } from "@/api/types/doctor.types";

/**
 * 예약 환자 목록 조회
 * GET /hospital-staff/reservation-list
 * @param date YYYY-MM-DD
 */
export const getReservationList = async (date: string) => {
    console.log(`📡 [API] 예약 목록 조회 요청: ${date}`);
    const response = await api.get<ApiResponseListReservationListResponse>(
        '/hospital-staff/reservation-list',
        {
            params: { date }
        }
    );
    return response.data;
};
