// src/features/doctor/types/doctor.ts

// 1. 환자 목록 (대기열)용 DTO
export interface PatientDto {
  childId: string;
  hospitalChildrenId?: string; // 선택적
  name: string;       // 화면 표시용 이름 (API의 childName 매핑)
  childName?: string; // API 원본 필드 대응
  gender: string;
  monthlyAge: number; // 화면 표시용 (API의 months 매핑)
  months?: number;    // API 원본 필드 대응
  birthdate?: string;
}

// 2. 환자 상세 정보 (PatientDetailPanel용)
export interface PatientHistory {
  category: string;
  content: string;
}

export interface PatientDetailFull {
  name: string;
  gender: "MALE" | "FEMALE";
  monthlyAge: number;
  birthdate: string;
  height: string;
  weight: string;
  caregiver: string;
  medication: string;
  familyHistory: string;
  history: PatientHistory[];
  complaints: PatientHistory[];
}

// 3. UI용 분석 타임스탬프 (CentralAnalysisPanel용)
export interface AnalysisTimestamp {
  id: number;
  type: "parent" | "child-vocal" | "child-behavior"; // 타임라인 색상/위치 결정
  label: string;
  detail?: string; // 툴팁용 상세 설명
  startTime: number;
  duration: number;
}

// 4. 타임라인 행 설정 타입 (이 부분이 누락되어 에러 발생함)
export interface TimelineRowConfig {
  key: string;
  label: string;
  color: string;
}

// 5. 비디오 분석 데이터 통합 (DoctorDashboard -> CentralAnalysisPanel)
export interface VideoAnalysisData {
  videoUrl: string | null; // 영상이 없을 수 있음 (null 허용)
  totalDuration: number;
  timestamps: AnalysisTimestamp[];
  rows: TimelineRowConfig[]; // 동적 타임라인 행 설정
}