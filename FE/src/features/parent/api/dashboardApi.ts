import api from '@/api/axiosConfig';
import type {
    ChildHomeResponse,
    ChildHospitalLinkRequest,
    HospitalResponseDto,
    ApiResponseChildHome,
    ApiResponseChildHospitalList
} from '@/api/types/child.types';

// =================================================================
// 테스트용 UUID (localStorage에 selectedChildId가 없을 때 fallback)
// =================================================================
export const TEST_CHILD_ID = "136d8eb8-8264-4953-9c9c-19baf49dc8b4";

// =================================================================
// Re-export types for backward compatibility
// =================================================================
export type { ChildDashboardStatus } from '@/api/types';
export type { ChildHomeResponse, HospitalInfoDTO as LinkedHospital } from '@/api/types/child.types';


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


