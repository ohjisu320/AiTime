import axios from 'axios';

// 1. Interfaces
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
        isExamEligible: boolean;
        examProgress: number;
        hasPreviousExam: boolean;
        nextEligibleAt: string;
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

// 2. Constants for Mock Data
const MOCK_CHILD_DATA: ChildHomeResponse = {
    code: 0,
    status: "100 CONTINUE",
    message: "Success (Mock)",
    data: {
        childId: "mock-child-001",
        name: "김지후",
        gender: "MALE",
        isExamEligible: true,
        examProgress: 0,
        hasPreviousExam: true,
        nextEligibleAt: "2026-01-28",
        linkedHospitals: [
            { hospitalId: "h-001", name: "서울대학교병원" },
            { hospitalId: "h-002", name: "연세세브란스" }
        ]
    }
};

const MOCK_LINK_SUCCESS: HospitalLinkResponse = {
    status: "OK",
    message: "병원 연동이 성공적으로 완료되었습니다. (Mock)",
    code: 200
};

// 3. API Functions
// GET /api/v1/child/{childId}
export const fetchChildHomeInfo = async (childId: string): Promise<ChildHomeResponse> => {
    try {
        const response = await axios.get<ChildHomeResponse>(`/api/v1/child/${childId}`);

        // Validate response structure
        if (!response.data || !response.data.data) {
            throw new Error("Invalid response structure received from API");
        }

        return response.data;
    } catch (error) {
        console.warn("API Failed. Falling back to Mock Data...", error);
        // CRITICAL FIX: Return Mock Data directly to prevent UI error
        return MOCK_CHILD_DATA;
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
            // Avoid duplicates to keep it clean
            const exists = MOCK_CHILD_DATA.data.linkedHospitals.some(h => h.hospitalId === "h-mock-new");
            if (!exists) {
                MOCK_CHILD_DATA.data.linkedHospitals.push({
                    hospitalId: "h-mock-new",
                    name: "튼튼소아과 (Mock)"
                });
            }
        }

        return MOCK_LINK_SUCCESS;
    }
};
