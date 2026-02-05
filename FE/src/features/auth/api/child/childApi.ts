// src/features/api/child/childApi.ts
import api from "@/api/axiosConfig";
import type {
  ApiResponse,
  ChildListResponse,
  ChildCreateRequest,
  ChildInfoResponse,
  ChildHomeData,
  ChildHomeResponse,
  ChildDashboardStatus,
  LinkedHospital,
  HospitalResponseDto,
  HospitalLinkRequest,
} from "./types";

// =================================================================
// 테스트용 UUID (localStorage에 selectedChildId가 없을 때 fallback)
// =================================================================
export const TEST_CHILD_ID = "136d8eb8-8264-4953-9c9c-19baf49dc8b4";

// =================================================================
// [API Functions]
// =================================================================

/**
 * 0. 자녀 목록 조회 (GET) - 프로필 선택 페이지용
 */
export const getChildren = async (): Promise<ChildListResponse> => {
  console.log("🚀 [GET] Fetching Children List...");
  try {
    const response = await api.get<ApiResponse<ChildListResponse>>("/child");
    // data.data가 배열입니다.
    console.log("✅ Children List Success:", response.data.data);
    return response.data.data;
  } catch (error) {
    console.error("❌ getChildren Error:", error);
    throw error;
  }
};

/**
 * 0. 자녀 등록 (POST)
 */
export const addChild = async (
  data: ChildCreateRequest,
): Promise<ChildInfoResponse> => {
  console.log("🚀 [POST] Adding Child:", data);
  try {
    const response = await api.post<ApiResponse<ChildInfoResponse>>(
      "/child",
      data,
    );
    return response.data.data;
  } catch (error) {
    console.error("❌ addChild Error:", error);
    throw error;
  }
};

/**
 * 1. 메인 대시보드 정보 조회 (GET)
 * (에러 발생 시 Mock 데이터를 반환하지 않고 throw 하되, 필요시 컴포넌트에서 처리)
 */
export const fetchChildHomeInfo = async (
  childId: string,
): Promise<ChildHomeData> => {
  const targetId = childId || TEST_CHILD_ID;
  console.log(`🚀 [GET] Dashboard Info for: ${targetId}`);

  try {
    const response = await api.get<ChildHomeResponse>(`/child/${targetId}`);
    console.log("✅ Fetch Success:", response.data);
    return response.data.data;
  } catch (error) {
    console.error("❌ fetchChildHomeInfo Error:", error);
    throw error;
  }
};

/**
 * 2. 연결된 병원 목록 조회 (GET)
 */
export const fetchLinkedHospitals = async (
  childId: string,
): Promise<HospitalResponseDto[]> => {
  const targetId = childId || TEST_CHILD_ID;
  console.log(`🚀 [GET] Hospital List for: ${targetId}`);

  try {
    const response = await api.get<ApiResponse<HospitalResponseDto[]>>(
      `/child/${targetId}/hospital-list`,
    );
    const list = response.data?.data || [];
    console.log("✅ Linked Hospitals:", list);
    return list;
  } catch (error) {
    console.error("❌ fetchLinkedHospitals Error:", error);
    return []; // 에러 시 빈 배열 반환
  }
};

/**
 * 3. 초대코드로 병원 연결 (POST)
 */
export const registerInviteCode = async (
  childId: string,
  inviteCode: string,
) => {
  const targetId = childId || TEST_CHILD_ID;
  console.log(
    `🚀 [POST] Linking Hospital... Child: ${targetId}, Code: ${inviteCode}`,
  );

  const requestBody: HospitalLinkRequest = { inviteCode };

  try {
    const response = await api.post(
      `/child/${targetId}/hospital-link`,
      requestBody,
    );
    console.log("✅ Link Success:", response.data);
    return response.data;
  } catch (error: any) {
    console.error("❌ registerInviteCode Error:", error);
    throw error;
  }
};

/**
 * 4. 자녀 삭제 (DELETE)
 */
export const deleteChild = async (childId: string): Promise<void> => {
  console.log(`🚀 [DELETE] Deleting Child: ${childId}`);
  try {
    await api.delete<ApiResponse<void>>(`/child/${childId}`);
    console.log(`✅ Delete Success: ${childId}`);
  } catch (error) {
    console.error('❌ deleteChild Error:', error);
    throw error;
  }
};

// =================================================================
// 🚨 [Mock Data Exports]
// useParentDashboard.ts 등의 다른 파일 의존성을 위해 유지
// =================================================================

const MOCK_BASE_DATA = {
  childId: TEST_CHILD_ID,
  examId: null,
  name: "오하나",
  gender: "FEMALE" as const,
  examStatus: "AVAILABLE" as ChildDashboardStatus,
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
  data: MOCK_BASE_DATA,
};

export const MOCK_CASE_WAITING: ChildHomeResponse = {
  code: 200,
  status: "OK",
  message: "Success",
  data: { ...MOCK_BASE_DATA, examStatus: "WAITING", examProgress: 2 },
};

export const MOCK_CASE_COOLDOWN: ChildHomeResponse = {
  code: 200,
  status: "OK",
  message: "Success",
  data: { ...MOCK_BASE_DATA, examStatus: "COOLDOWN", examProgress: 4 },
};

export const MOCK_CASE_NEED_HOSPITAL: ChildHomeResponse = {
  code: 200,
  status: "OK",
  message: "Success",
  data: { ...MOCK_BASE_DATA, examStatus: "NEED_HOSPITAL", linkedHospitals: [] },
};

export const MOCK_CASE_COOLDOWN_BEFORE: ChildHomeResponse = {
  code: 200,
  status: "OK",
  message: "Success",
  data: { ...MOCK_BASE_DATA, examStatus: "COOLDOWN_BEFORE", examProgress: 4 },
};

export const MOCK_CASE_IN_PROGRESS: ChildHomeResponse = {
  code: 200,
  status: "OK",
  message: "Success",
  data: { ...MOCK_BASE_DATA, examStatus: "IN_PROGRESS", examProgress: 2 },
};
