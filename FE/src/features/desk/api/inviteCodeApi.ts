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
    console.log(`📡 [API] 미등록 환자 조회 요청: ${year}-${month}-${day}`);
    const response = await api.get<ApiResponseUnregisteredPatients>(
        `/invite-code/patients`,
        {
            params: { year, month, day },
        }
    );

    return response.data;
    return response.data;
};

import type { ApiResponseInviteCode, InviteCodeRequest } from "@/api/types/inviteCode.types";

/**
 * 초대코드 생성 (발급)
 * POST /invite-code
 */
export const createInviteCode = async (data: InviteCodeRequest) => {
    console.log(`📡 [API] 초대코드 발급 요청:`, data);
    const response = await api.post<ApiResponseInviteCode>(
        `/invite-code`,
        data
    );
    return response.data;
};
