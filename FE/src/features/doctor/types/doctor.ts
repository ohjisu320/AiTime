// src/features/doctor/types/doctor.ts

// [1. API 명세 기반 데이터 타입]
export interface PatientDto {
  childId: string;
  userId: string;
  name: string;
  monthlyAge: number;
  birthdate: string; // 'YYYY-MM-DD'
  gender: 'MALE' | 'FEMALE';
  latestExamStatus: string;
}

export interface PatientSearchResponse {
  childResponses: PatientDto[];
  total: number;
}

// [추가됨] API 응답 래퍼 타입 정의
export interface ApiResponsePatientSearchResponse {
  code: number;
  status: string;
  message: string;
  data: PatientSearchResponse;
}

// [2. Static Mock Data Types]
export interface PatientDetailFull extends PatientDto {
  height: string;
  weight: string;
  caregiver: string;
  medication: string;
  familyHistory: string;
  history: { category: string; content: string }[];
  complaints: { category: string; content: string }[];
}

export interface TimelineMarker {
  type: 'parent' | 'child-vocal' | 'child-behavior';
  label: string;
  start: number;
  width: number;
}

export interface AdosItem {
  name: string;
  score: number;
  checked: boolean;
}

export interface AdosCategory {
  title: string;
  items: AdosItem[];
}

export interface AnalysisTimestamp {
id: number;
type: 'parent' | 'child-vocal' | 'child-behavior'; // 타임라인 행 구분용
label: string;      // 마커 이름 (예: 호명반응)
startTime: number;  // 시작 시간 (초)
duration: number;   // 지속 시간 (초)
}

export interface VideoAnalysisData {
videoUrl: string;       // 영상 URL
totalDuration: number;  // 영상 전체 길이 (초)
timestamps: AnalysisTimestamp[];
}