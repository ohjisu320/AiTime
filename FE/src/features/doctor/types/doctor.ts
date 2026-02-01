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