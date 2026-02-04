import api from '@/api/axiosConfig';

// =================================================================
// 테스트용 UUID (localStorage에 selectedChildId가 없을 때 fallback)
// =================================================================
export const TEST_CHILD_ID = "136d8eb8-8264-4953-9c9c-19baf49dc8b4";

// =================================================================
// 타입 정의 (Type Definitions)
// =================================================================

export type ChildDashboardStatus =
    | 'NEED_HOSPITAL'       // 병원 연결 필요
    | 'AVAILABLE'           // 새 검사 가능
    | 'AVAILABLE_EXPIRED'   // 검사 가능 (이전 임시저장 만료됨)
    | 'IN_PROGRESS'         // 검사 진행 중 (이어하기)
    | 'COOLDOWN'            // 쿨타임 (다음 검사 대기)
    | 'COOLDOWN_BEFORE'     // 쿨타임 중 병원 연동됨 (특수 케이스)
    | 'WAITING';            // 대기 중

export interface LinkedHospital {
    hospitalId: string;
    name: string;
}

export interface ChildHomeResponse {
    code: number;
    status: string;
    message: string;
    data: {
        childId: string;
        examId: string | null;             // ✅ 추가: 현재 진행 중인 검사 ID
        name: string;
        gender: 'MALE' | 'FEMALE';
        examStartedAt: string | null;      // ✅ 추가
        examStatus: ChildDashboardStatus;  // ✅ examStatus (API 명세)
        examProgress: number;
        draftExpiresAt: string | null;
        nextEligibleAt: string | null;
        linkedHospitals: LinkedHospital[];
    };
}

export interface HospitalLinkRequest {
    inviteCode: string;
}

export interface HospitalLinkResponse {
    code: number;
    status: string;
    message: string;
    data?: string;
}


// --- [API Functions] ---------------------------------------------

/**
 * 1. 메인 대시보드 정보 조회 (GET)
 * (수정사항: API 에러가 나면 무조건 Mock 데이터를 반환해서 화면이 꺼지지 않게 함)
 */
export const fetchChildHomeInfo = async (childId: string) => {
    // childId가 없거나 이상하면 테스트 ID로 대체
    const targetId = childId || TEST_CHILD_ID;
    console.log(`🚀 [GET] Dashboard Info for: ${targetId}`);

    try {
        const response = await api.get(`/child/${targetId}`);
        console.log("✅ Fetch Success:", response.data);
        // API 응답 구조: {code, status, message, data: {...child info...}}
        // 실제 아이 정보만 반환
        return response.data.data;
    } catch (error) {
        console.error("❌ fetchChildHomeInfo Error:", error);
        throw error; // 에러를 그대로 던짐 → 에러 화면 표시
    }
};

/**
 * 2. 연결된 병원 목록 조회 (GET)
 */
export const fetchLinkedHospitals = async (childId: string) => {
    const targetId = childId || TEST_CHILD_ID;
    console.log(`🚀 [GET] Hospital List for: ${targetId}`);

    try {
        const response = await api.get(`/child/${targetId}/hospital-list`);

        // Swagger 명세상 data.data 안에 배열이 있었음
        const list = response.data?.data || [];
        console.log("✅ Linked Hospitals:", list);
        return list;
    } catch (error) {
        console.error("❌ fetchLinkedHospitals Error:", error);
        return []; // 에러 시 빈 배열 반환하여 화면 안 깨지게 처리
    }
};

/**
 * 3. 초대코드로 병원 연결 (POST)
 */
export const registerInviteCode = async (childId: string, inviteCode: string) => {
    const targetId = childId || TEST_CHILD_ID;
    console.log(`🚀 [POST] Linking Hospital... Child: ${targetId}, Code: ${inviteCode}`);

    const requestBody = { inviteCode };
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
        // 에러 응답 상세 정보 출력
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

const MOCK_BASE_DATA = {
    childId: TEST_CHILD_ID,
    examId: null,
    name: "오하나",
    gender: "FEMALE" as const,
    examStatus: "AVAILABLE" as ChildDashboardStatus,  // ✅ examStatus
    examProgress: 0,
    examStartedAt: null,
    nextEligibleAt: null,
    draftExpiresAt: null,
    linkedHospitals: [] as LinkedHospital[],
};

export const MOCK_CASE_AVAILABLE: ChildHomeResponse = {
    code: 200,
    status: "OK",
    message: "Success",
    data: MOCK_BASE_DATA
};

export const MOCK_CASE_WAITING: ChildHomeResponse = {
    code: 200,
    status: "OK",
    message: "Success",
    data: { ...MOCK_BASE_DATA, examStatus: "WAITING", examProgress: 2 }
};

export const MOCK_CASE_COOLDOWN: ChildHomeResponse = {
    code: 200,
    status: "OK",
    message: "Success",
    data: { ...MOCK_BASE_DATA, examStatus: "COOLDOWN", examProgress: 4 }
};

export const MOCK_CASE_NEED_HOSPITAL: ChildHomeResponse = {
    code: 200,
    status: "OK",
    message: "Success",
    data: { ...MOCK_BASE_DATA, examStatus: "NEED_HOSPITAL", linkedHospitals: [] }
};

export const MOCK_CASE_COOLDOWN_BEFORE: ChildHomeResponse = {
    code: 200,
    status: "OK",
    message: "Success",
    data: { ...MOCK_BASE_DATA, examStatus: "COOLDOWN_BEFORE", examProgress: 4 }
};

export const MOCK_CASE_IN_PROGRESS: ChildHomeResponse = {
    code: 200,
    status: "OK",
    message: "Success",
    data: { ...MOCK_BASE_DATA, examStatus: "IN_PROGRESS", examProgress: 2 }
};
