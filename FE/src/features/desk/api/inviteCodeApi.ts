import api from "@/api/axiosConfig";
import type { ApiResponseUnregisteredPatients, ApiResponseCalendar, ApiResponseInviteCode, InviteCodeRequest, ApiResponseInviteCodeRevoke } from "@/api/types/inviteCode.types";

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
};

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

/**
 * 예약 캘린더 조회 (월별 점 표시)
 * GET /invite-code/calendar
 * @param year 년도
 * @param month 월
 */
export const getScheduledDates = async (year: number, month: number) => {
    console.log(`📡 [API] 예약 캘린더 조회: ${year}-${month}`);
    const response = await api.get<ApiResponseCalendar>(
        '/invite-code/calendar',
        { params: { year, month } }
    );
    return response.data;
};

/**
 * 초대코드 취소 (삭제)
 * DELETE /invite-code/{inviteCodeId}
 */
export const revokeInviteCode = async (inviteCodeId: string) => {
    console.log(`📡 [API] 초대코드 취소 요청: ${inviteCodeId}`);
    const response = await api.delete<ApiResponseInviteCodeRevoke>(
        `/invite-code/${inviteCodeId}`
    );
    return response.data;
};
