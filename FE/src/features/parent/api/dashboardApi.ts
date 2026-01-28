import axios from 'axios';

// ---------------------------
// 1. Enums & Interfaces
// ---------------------------

export type ChildDashboardStatus =
    | 'NEED_HOSPITAL'       // 병원 연결 필요
    | 'AVAILABLE'           // 새 검사 가능
    | 'AVAILABLE_EXPIRED'   // 검사 가능 (이전 임시저장 만료됨)
    | 'IN_PROGRESS'         // 검사 진행 중 (이어하기)
    | 'COOLDOWN'            // 쿨타임 (다음 검사 대기)
    | 'COOLDOWN_BEFORE';    // 쿨타임 중 병원 연동됨 (특수 케이스)

export interface LinkedHospital {
    hospitalId: string;
    name: string;
}

export interface ChildHomeResponse {
    code: number;
    status: string; // API 응답 status (e.g., "200 OK")
    message: string;
    data: {
        childId: string;
        name: string;
        gender: 'MALE' | 'FEMALE';
        status: ChildDashboardStatus; // UI 상태 결정용 핵심 필드
        isExamEligible: boolean;
        examProgress: number; // 0 ~ 4
        hasPreviousExam: boolean;
        draftExpiresAt: string | null; // ISO Date String
        nextEligibleAt: string | null; // ISO Date String
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
}

// ---------------------------
// 2. Constants for Mock Data (Scenarios)
// ---------------------------

const BASE_CHILD_DATA = {
    childId: "mock-child-001",
    name: "김지후",
    gender: "MALE" as const,
    hasPreviousExam: true,
};

// Case 1: 병원 연결 필요
export const MOCK_CASE_NEED_HOSPITAL: ChildHomeResponse = {
    code: 200, status: "OK", message: "Success",
    data: {
        ...BASE_CHILD_DATA,
        status: 'NEED_HOSPITAL',
        isExamEligible: false,
        examProgress: 0,
        draftExpiresAt: null,
        nextEligibleAt: null,
        linkedHospitals: []
    }
};

// Case 2: 새 검사 가능 (기본)
export const MOCK_CASE_AVAILABLE: ChildHomeResponse = {
    code: 200, status: "OK", message: "Success",
    data: {
        ...BASE_CHILD_DATA,
        status: 'IN_PROGRESS',
        isExamEligible: true,
        examProgress: 2,
        draftExpiresAt: null,
        nextEligibleAt: null,
        linkedHospitals: [{ hospitalId: "h1", name: "서울대학교병원" }]
    }
};

// Case 3: 새 검사 가능 (이전 임시저장 만료) - 모달 띄우기용
export const MOCK_CASE_AVAILABLE_EXPIRED: ChildHomeResponse = {
    code: 200, status: "OK", message: "Success",
    data: {
        ...BASE_CHILD_DATA,
        status: 'AVAILABLE_EXPIRED',
        isExamEligible: true,
        examProgress: 0,
        draftExpiresAt: null,
        nextEligibleAt: null,
        linkedHospitals: [{ hospitalId: "h1", name: "서울대학교병원" }]
    }
};

// Case 4: 검사 진행 중 (이어하기)
const twoDaysFromNow = new Date();
twoDaysFromNow.setDate(twoDaysFromNow.getDate() + 2);

export const MOCK_CASE_IN_PROGRESS: ChildHomeResponse = {
    code: 200, status: "OK", message: "Success",
    data: {
        ...BASE_CHILD_DATA,
        status: 'IN_PROGRESS',
        isExamEligible: true, // 진행 중이어도 eligible은 true일 수 있음 (컨텍스트에 따라 다름)
        examProgress: 2, // 2/4 단계 진행 중
        draftExpiresAt: twoDaysFromNow.toISOString(),
        nextEligibleAt: null,
        linkedHospitals: [{ hospitalId: "h1", name: "서울대학교병원" }]
    }
};

// Case 5: 쿨타임 (검사 완료, 대기 중) - Read Only
export const MOCK_CASE_COOLDOWN: ChildHomeResponse = {
    code: 200, status: "OK", message: "Success",
    data: {
        ...BASE_CHILD_DATA,
        status: 'COOLDOWN',
        isExamEligible: false,
        examProgress: 4, // 완료
        draftExpiresAt: null,
        nextEligibleAt: "2026-05-30", // 미래 날짜
        linkedHospitals: [{ hospitalId: "h1", name: "서울대학교병원" }]
    }
};

// Case 6: 쿨타임 중 병원 연동됨 (제출 제안 모달)
export const MOCK_CASE_COOLDOWN_BEFORE: ChildHomeResponse = {
    code: 200, status: "OK", message: "Success",
    data: {
        ...BASE_CHILD_DATA,
        status: 'COOLDOWN_BEFORE',
        isExamEligible: false,
        examProgress: 4,
        draftExpiresAt: null,
        nextEligibleAt: "2026-05-30",
        linkedHospitals: [{ hospitalId: "h1", name: "서울대학교병원" }]
    }
};

// ---------------------------
// 3. API Functions
// ---------------------------

// GET /api/v1/child/{childId}
export const fetchChildHomeInfo = async (childId: string): Promise<ChildHomeResponse> => {
    try {
        const response = await axios.get<ChildHomeResponse>(`/api/v1/child/${childId}`);

        if (!response.data || !response.data.data) {
            throw new Error("Invalid response structure received from API");
        }

        return response.data;
    } catch (error) {
        console.warn("API Failed. Falling back to Mock Data...", error);

        // ---------------------------------------------------------
        // [DEVELOPER] Uncomment ONE line below to test specific status
        // ---------------------------------------------------------

        // return MOCK_CASE_NEED_HOSPITAL;      // Case 1: 병원 없음
        return MOCK_CASE_AVAILABLE;          // Case 2: 검사 가능 (기본)
        // return MOCK_CASE_AVAILABLE_EXPIRED;  // Case 3: 만료 재검사
        // return MOCK_CASE_IN_PROGRESS;        // Case 4: 이어하기
        // return MOCK_CASE_COOLDOWN;           // Case 5: 완료/대기 (영상 보기)
        // return MOCK_CASE_COOLDOWN_BEFORE;    // Case 6: 기존 영상 제출 제안

        // Default Fallback
        // return MOCK_CASE_AVAILABLE;
    }
};

// POST /api/v1/child/{childId}/hospital-link
export const registerInviteCode = async (childId: string, inviteCode: string): Promise<HospitalLinkResponse> => {
    try {
        const response = await axios.post<HospitalLinkResponse>(`/api/v1/child/${childId}/hospital-link`, {
            inviteCode
        });
        return response.data;
    } catch (error) {
        console.warn("registerInviteCode failed, using MOCK DATA", error);

        // MOCK LOGIC: Update the in-memory mock data so the UI reflects the change
        if (inviteCode === "AAA") {
            const newHospital = { hospitalId: "h-mock-new", name: "튼튼소아과 (Mock)" };

            // Helper to add hospital if not exists
            const addHospital = (target: ChildHomeResponse) => {
                if (!target.data.linkedHospitals.some(h => h.hospitalId === "h-mock-new")) {
                    target.data.linkedHospitals.push(newHospital);
                }
            };

            // Update ALL mock cases to ensure the user sees the change regardless of which one is active
            addHospital(MOCK_CASE_NEED_HOSPITAL);
            addHospital(MOCK_CASE_AVAILABLE);
            addHospital(MOCK_CASE_AVAILABLE_EXPIRED);
            addHospital(MOCK_CASE_IN_PROGRESS);
            addHospital(MOCK_CASE_COOLDOWN);
            addHospital(MOCK_CASE_COOLDOWN_BEFORE);

            // Special State Transitions (Optional enhancement)
            // If we were in NEED_HOSPITAL, we are now AVAILABLE (if eligible)
            if (MOCK_CASE_NEED_HOSPITAL.data.status === 'NEED_HOSPITAL') {
                // For now, let's not auto-change status to avoid confusion, 
                // but typically this would become AVAILABLE.
            }
        }

        // Simple Mock Response
        return {
            code: 200,
            status: "OK",
            message: "병원 연동이 성공적으로 완료되었습니다. (Mock)"
        };
    }
};
