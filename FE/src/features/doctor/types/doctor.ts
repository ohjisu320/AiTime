// src/features/doctor/types/doctor.ts
/**
 * 의사 기능 타입 정의
 * OpenAPI 명세서 기반 (2026-02-05)
 */

// ===== Enum Types =====

export type VideoType = 'TASK1' | 'TASK2' | 'TASK3' | 'TASK4';
export type VideoStatus = 'UPLOADED' | 'ANALYZING' | 'FAILED' | 'EMPTY';
export type ExamStatus = 'IN_PROGRESS' | 'COMPLETED';

// ===== API Response Types =====

export interface PatientDto {
  childId: string;
  // [추가] 병원-환아 매핑 ID (API 응답에 이 필드가 있는지 확인 필요)
  hospitalChildrenId?: string;
  userId: string;
  name: string;
  monthlyAge: number;
  birthdate: string;
  gender: 'MALE' | 'FEMALE';
  latestExamStatus: string;
}

export interface PatientSearchResponse {
  childResponses: PatientDto[];
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

export interface DoctorDashboardData {
  taskType: VideoType;
  analysisScores: AnalysisScore[];
  examHistory: ExamHistoryItem[];
}

export interface VideoByDateItem {
  videoId: string;      // UUID
  videoType: VideoType;
  status: VideoStatus;
  durationSec?: number | null;
}

export interface TaskVideoItem {
  examDate: string;     // YYYY-MM-DD
  videoId: string;      // UUID
  status: VideoStatus;
  analysisResult?: Record<string, unknown> | null;
}

// ===== Patient Detail Types =====

export interface PatientDetailFull extends PatientDto {
  height: string;
  weight: string;
  caregiver: string;
  medication: string;
  familyHistory: string;
  history: { category: string; content: string }[];
  complaints: { category: string; content: string }[];
}

// ===== Video Analysis Types =====

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
  type: 'parent' | 'child-vocal' | 'child-behavior';
  label: string;
  startTime: number;
  duration: number;
}

export interface VideoAnalysisData {
  videoUrl: string;
  totalDuration: number;
  timestamps: AnalysisTimestamp[];
}