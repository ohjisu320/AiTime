import axios from 'axios';

// =================================================================
// 🚨 DEBUGGING MODE: HARDCODED CONFIGURATION
// 설정 파일(axiosConfig)을 거치지 않고 직접 요청을 보냅니다.
// 테스트가 끝나면 나중에 다시 원래대로 복구해야 합니다.
// =================================================================

// 1. 여기에 진짜 토큰 넣기
// (Bearer라는 글자는 빼고 토큰 문자열만 넣으세요)
const REAL_TOKEN = "진짜 토큰 넣기";

// 2. 테스트용 UUID (필요 시 사용)
export const TEST_CHILD_ID = "3fa85f64-5717-4562-b3fc-2c963f66afa6";

// 3. API 기본 도메인 (절대 경로)
const API_BASE_URL = "https://i14a501.p.ssafy.io/api/v1";

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
        name: string;
        gender: 'MALE' | 'FEMALE';
        status: ChildDashboardStatus;
        isExamEligible: boolean;
        examProgress: number;
        hasPreviousExam: boolean;
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
        const response = await axios.get(
            `${API_BASE_URL}/child/${targetId}`,
            {
                headers: {
                    'Authorization': `Bearer ${REAL_TOKEN}`,
                    'Content-Type': 'application/json'
                }
            }
        );
        console.log("✅ Fetch Success:", response.data);
        // API 응답 구조에 따라 data.data 혹은 data를 반환
        return response.data?.data || response.data;
    } catch (error) {
        // 🚨 여기가 핵심입니다! 
        // 에러를 throw 하지 않고, 콘솔에만 찍은 뒤 '가짜 데이터'를 리턴합니다.
        console.warn("⚠️ API 연결 실패 (401 등). 임시 데이터를 보여줍니다.");
        console.error("❌ fetchChildHomeInfo Error:", error);

        // 화면이 죽지 않도록 Mock Data 반환
        return MOCK_CASE_AVAILABLE;
    }
};

/**
 * 2. 연결된 병원 목록 조회 (GET)
 */
export const fetchLinkedHospitals = async (childId: string) => {
    const targetId = childId || TEST_CHILD_ID;
    console.log(`🚀 [GET] Hospital List for: ${targetId}`);

    try {
        const response = await axios.get(
            `${API_BASE_URL}/child/${targetId}/hospital-list`,
            {
                headers: {
                    'Authorization': `Bearer ${REAL_TOKEN}`,
                    'Content-Type': 'application/json'
                }
            }
        );

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

    try {
        const response = await axios.post(
            `${API_BASE_URL}/child/${targetId}/hospital-link`,
            { inviteCode }, // Body
            {
                headers: {
                    'Authorization': `Bearer ${REAL_TOKEN}`,
                    'Content-Type': 'application/json'
                }
            }
        );

        console.log("✅ Link Success:", response.data);
        return response.data;
    } catch (error) {
        console.error("❌ registerInviteCode Error:", error);
        throw error;
    }
};

// =================================================================
// 🚨 [Fix] Missing Exports for Build Error
// useParentDashboard.ts 에서 import 하고 있는 Mock 상수들을 복구합니다.
// =================================================================

const MOCK_BASE_DATA = {
    childId: TEST_CHILD_ID,
    name: "오하나",
    gender: "FEMALE" as const,
    birthDate: "2019-05-05",
    hasPreviousExam: true,
    status: "AVAILABLE" as ChildDashboardStatus,
    isExamEligible: true,
    examProgress: 0,
    draftExpiresAt: null,
    nextEligibleAt: null,
    linkedHospitals: [] as LinkedHospital[],
    recentExamResult: null
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
    data: { ...MOCK_BASE_DATA, status: "WAITING", examProgress: 2 }
};

export const MOCK_CASE_COOLDOWN: ChildHomeResponse = {
    code: 200,
    status: "OK",
    message: "Success",
    data: { ...MOCK_BASE_DATA, status: "COOLDOWN", isExamEligible: false, examProgress: 4 }
};

export const MOCK_CASE_NEED_HOSPITAL: ChildHomeResponse = {
    code: 200,
    status: "OK",
    message: "Success",
    data: { ...MOCK_BASE_DATA, status: "NEED_HOSPITAL", linkedHospitals: [] }
};

export const MOCK_CASE_COOLDOWN_BEFORE: ChildHomeResponse = {
    code: 200,
    status: "OK",
    message: "Success",
    data: { ...MOCK_BASE_DATA, status: "COOLDOWN_BEFORE", isExamEligible: false, examProgress: 4 }
};

export const MOCK_CASE_IN_PROGRESS: ChildHomeResponse = {
    code: 200,
    status: "OK",
    message: "Success",
    data: { ...MOCK_BASE_DATA, status: "IN_PROGRESS", examProgress: 2 }
};
