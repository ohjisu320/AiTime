// src/features/doctor/types/doctor.ts

// ===== Enum Types =====

// 명세서 상 videoType은 문자열로 오지만, 프론트에서 관리하기 편하게 리터럴로 정의
// 백엔드가 실제로 보내는 값 확인 필요 (예: "POSE_IMITATION" 등일 수도 있음)
export type VideoType = 'TASK1' | 'TASK2' | 'TASK3' | 'TASK4' | string;
export type VideoStatus = 'UPLOADED' | 'ANALYZING' | 'FAILED' | 'EMPTY';
export type ExamStatus = 'IN_PROGRESS' | 'COMPLETED' | 'NEED_HOSPITAL' | 'AVAILABLE';

// ===== API Response Types (DTO) =====

/**
 * API: /doctor/patients (환자 검색) 결과 아이템
 * Schema: ChildResponse
 */
export interface PatientDto {
  // 명세서 필드 매핑
  hospitalChildrenId: string; // UUID (필수)
  childName: string;          // 명세서: childName (주의: name 아님)
  gender: 'MALE' | 'FEMALE';
  months: number;             // 명세서: months (주의: monthlyAge 아님)

  // 아래 필드들은 명세서의 ChildResponse에는 있지만
  // 검색 결과 목록에는 없을 수도 있음. 확인 필요.
  childId?: string;
  scheduledAt?: string;       // YYYY-MM-DDTHH:mm:ss
  examStatus?: string;
  isSubmitted?: boolean;

  // 프론트엔드 편의를 위해 매핑해서 쓸 필드 (옵션)
  birthdate?: string;         // API에는 없으므로 계산하거나 더미데이터 사용 시 필요
}

export interface PatientSearchResponse {
  // [수정] 로그 기준: childResponses -> data
  data: PatientDto[];
  total: number;
}

export interface ApiResponsePatientSearchResponse {
  code: number;
  status: string;
  message: string;
  data: PatientSearchResponse;
}

// ===== Dashboard Types (OpenAPI) =====

export interface AnalysisScore {
  date: string;      // YYYY-MM-DD
  score: number;
  examId: string;    // UUID
}

export interface ExamHistoryItem {
  examId: string;       // UUID
  completedAt: string;  // YYYY-MM-DD
  status: ExamStatus;
}

// ===== Patient Detail Types (Composite) =====

/**
 * 환자 목록의 DTO 정보 + 추가 상세 정보(더미 데이터 등)를 합친 UI용 타입
 */
export interface PatientDetailFull {
  // PatientDto의 핵심 필드 상속
  hospitalChildrenId: string;
  childId?: string;
  name: string;           // UI에서 편하게 쓰기 위해 childName을 매핑할 필드
  monthlyAge: number;     // UI에서 편하게 쓰기 위해 months를 매핑할 필드
  gender: 'MALE' | 'FEMALE';
  birthdate: string;      // 더미/계산값

  // 상세 정보 (API 미지원으로 더미 사용 중인 필드들)
  height: string;
  weight: string;
  caregiver: string;
  medication: string;
  familyHistory: string;
  history: { category: string; content: string }[];
  complaints: { category: string; content: string }[];
}

// ===== Video Analysis Types (UI State) =====

/**
 * 프론트엔드 비디오 플레이어 타임라인 마커용 타입
 * (API 응답 TimestampDTO -> 이 타입으로 변환하여 사용)
 */
export interface AnalysisTimestamp {
  id: number;
  type: 'parent' | 'child-vocal' | 'child-behavior';
  label: string;
  startTime: number; // API의 startS
  duration: number;  // API의 endS - startS
}

export interface VideoAnalysisData {
  videoUrl: string;
  totalDuration: number;
  timestamps: AnalysisTimestamp[];
}