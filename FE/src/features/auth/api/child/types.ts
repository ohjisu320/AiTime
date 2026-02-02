// src/features/api/child/types.ts

// =================================================================
// 공통 응답 타입
// =================================================================
export interface ApiResponse<T> {
  code: number;
  status: string;
  message: string;
  data: T;
}

// =================================================================
// 자녀 목록 조회용 (ProfileSelectPage)
// =================================================================
export interface ChildInfoResponse {
  childId: string;
  name: string;
  months: number;
  gender: "MALE" | "FEMALE";
}

export type ChildListResponse = ChildInfoResponse[];

// =================================================================
// 자녀 생성용
// =================================================================
export interface ChildCreateRequest {
  name: string;
  birthdate: string; // YYYY-MM-DD
  gender: "MALE" | "FEMALE";
}

// =================================================================
// 자녀 대시보드(상세)용 (ChildDashboard)
// =================================================================
export type ChildDashboardStatus =
  | "NEED_HOSPITAL" // 병원 연결 필요
  | "AVAILABLE" // 새 검사 가능
  | "AVAILABLE_EXPIRED" // 검사 가능 (이전 임시저장 만료됨)
  | "IN_PROGRESS" // 검사 진행 중 (이어하기)
  | "COOLDOWN" // 쿨타임 (다음 검사 대기)
  | "COOLDOWN_BEFORE" // 쿨타임 중 병원 연동됨 (특수 케이스)
  | "WAITING"; // 대기 중

export interface LinkedHospital {
  hospitalId: string;
  name: string;
}

// 대시보드 정보 전체 구조
export interface ChildHomeData {
  childId: string;
  examId: string | null;
  name: string;
  gender: "MALE" | "FEMALE";
  examStartedAt: string | null;
  examStatus: ChildDashboardStatus;
  examProgress: number;
  draftExpiresAt: string | null;
  nextEligibleAt: string | null;
  linkedHospitals: LinkedHospital[];
}

// API 응답 래퍼 (Dashboard)
export interface ChildHomeResponse {
  code: number;
  status: string;
  message: string;
  data: ChildHomeData;
}

// =================================================================
// 병원 연동 관련
// =================================================================
export interface HospitalResponseDto {
  hospitalId: string;
  name: string;
  address: string;
  phoneNumber: string;
  linkStatus: "ACTIVE" | "INACTIVE";
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
