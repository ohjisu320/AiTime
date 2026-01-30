import api from '@/api/axiosConfig';
import type {
    ChildHomeResponse,
    ChildHospitalListResponse,
    ChildHospitalLinkRequest,
    HospitalResponseDto,
    ApiResponseChildHome,
    ApiResponseChildHospitalList
} from '@/api/types/child.types';
import { ChildDashboardStatus } from '@/api/types';

// =================================================================
// 테스트용 UUID (localStorage에 selectedChildId가 없을 때 fallback)
// =================================================================
export const TEST_CHILD_ID = "136d8eb8-8264-4953-9c9c-19baf49dc8b4";

// =================================================================
// 타입 정의 (Re-export for backward compatibility)
// =================================================================
export { ChildDashboardStatus };
export type { ChildHomeResponse };
export type LinkedHospital = HospitalResponseDto;

// --- [API Functions] ---------------------------------------------

/**
 * 1. 메인 대시보드 정보 조회 (GET)
 */
export const fetchChildHomeInfo = async (childId: string): Promise<ChildHomeResponse> => {
    // childId가 없거나 이상하면 테스트 ID로 대체
    const targetId = childId || TEST_CHILD_ID;
    console.log(`🚀 [GET] Dashboard Info for: ${targetId}`);

    try {
        const response = await api.get<ApiResponseChildHome>(`/child/${targetId}`);
        console.log("✅ Fetch Success:", response.data);
        // data.data가 실제 아이 정보
        return response.data.data;
    } catch (error) {
        console.error("❌ fetchChildHomeInfo Error:", error);
        throw error;
    }
};

/**
 * 2. 연결된 병원 목록 조회 (GET)
 */
export const fetchLinkedHospitals = async (childId: string): Promise<HospitalResponseDto[]> => {
    const targetId = childId || TEST_CHILD_ID;
    console.log(`🚀 [GET] Hospital List for: ${targetId}`);

    try {
        const response = await api.get<ApiResponseChildHospitalList>(`/child/${targetId}/hospital-list`);

        // Swagger 명세상 data.data 안에 배열이 있음
        const list = response.data.data?.data || [];
        console.log("✅ Linked Hospitals:", list);
        return list;
    } catch (error) {
        console.error("❌ fetchLinkedHospitals Error:", error);
        return [];
    }
};

/**
 * 3. 초대코드로 병원 연결 (POST)
 */
export const registerInviteCode = async (childId: string, inviteCode: string) => {
    const targetId = childId || TEST_CHILD_ID;
    console.log(`🚀 [POST] Linking Hospital... Child: ${targetId}, Code: ${inviteCode}`);

    const requestBody: ChildHospitalLinkRequest = { inviteCode };
    console.log('📤 Request Body:', JSON.stringify(requestBody));

    try {
        const response = await api.post(
            `/child/${targetId}/hospital-link`,
            requestBody
        );

        console.log("✅ Link Success:", response.data);
        return response.data;
    } catch (error: any) {
        console.error("❌ registerInviteCode Error:", error);
        if (error.response) {
            console.error("Error Response Data:", error.response.data);
            console.error("Error Response Status:", error.response.status);
        }
        throw error;
    }
};

// =================================================================
// 🚨 [Fix] Missing Exports for Build Error
// useParentDashboard.ts 에서 import 하고 있는 Mock 상수들을 복구합니다.
// =================================================================

const MOCK_BASE_DATA: ChildHomeResponse = {
    childId: TEST_CHILD_ID,
    name: "오하나",
    gender: "FEMALE",
    examStatus: "AVAILABLE",
    examProgress: 0,
    examStartedAt: null,
    nextEligibleAt: null,
    draftExpiresAt: null,
    linkedHospitals: [],
};

export const MOCK_CASE_AVAILABLE: ApiResponseChildHome = {
    code: 200,
    status: "200 OK",
    message: "Success",
    data: MOCK_BASE_DATA
};

export const MOCK_CASE_WAITING: ApiResponseChildHome = {
    code: 200,
    status: "200 OK",
    message: "Success",
    data: { ...MOCK_BASE_DATA, examStatus: "WAITING", examProgress: 2 }
};

export const MOCK_CASE_COOLDOWN: ApiResponseChildHome = {
    code: 200,
    status: "200 OK",
    message: "Success",
    data: { ...MOCK_BASE_DATA, examStatus: "COOLDOWN", examProgress: 4 }
};

export const MOCK_CASE_NEED_HOSPITAL: ApiResponseChildHome = {
    code: 200,
    status: "200 OK",
    message: "Success",
    data: { ...MOCK_BASE_DATA, examStatus: "NEED_HOSPITAL", linkedHospitals: [] }
};

export const MOCK_CASE_COOLDOWN_BEFORE: ApiResponseChildHome = {
    code: 200,
    status: "200 OK",
    message: "Success",
    data: { ...MOCK_BASE_DATA, examStatus: "COOLDOWN_BEFORE", examProgress: 4 }
};

export const MOCK_CASE_IN_PROGRESS: ApiResponseChildHome = {
    code: 200,
    status: "200 OK",
    message: "Success",
    data: { ...MOCK_BASE_DATA, examStatus: "IN_PROGRESS", examProgress: 2 }
};
