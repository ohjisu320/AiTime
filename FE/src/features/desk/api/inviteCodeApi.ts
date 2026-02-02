import api from "@/api/axiosConfig";
import type { ApiResponseUnregisteredPatients } from "@/api/types/inviteCode.types";

/**
 * 미등록 환자(대기열) 목록 조회
 * GET /invite-code/patients
 * @param year 년도
 * @param month 월
 * @param day 일
 */
export const getUnregisteredPatients = async (
    year: number,
    month: number,
    day: number
) => {
    const response = await api.get<ApiResponseUnregisteredPatients>(
        `/invite-code/patients`,
        {
            params: { year, month, day },
        }
    );

    return response.data;
};
