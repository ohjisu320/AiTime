/**
 * 의사 관련 API 타입 정의
 * Endpoints: /doctor/*, /hospital-staff/*
 */

import type { ApiResponse, UUID, ISODate } from '../types';

// =================================================================
// Doctor List (의사 목록)
// =================================================================

/**
 * 의사 목록 응답
 * GET /hospital-staff/doctors
 */
export interface DoctorListResponse {
    doctorId: UUID;
    doctorName: string;
}

export type ApiResponseDoctorList = ApiResponse<DoctorListResponse[]>;

// =================================================================
// Reservation Calendar (예약 캘린더)
// =================================================================

/**
 * 캘린더 요청 파라미터
 * GET /doctor/reservations/calendar
 */
export interface CalendarRequest {
    year: number;  // 2000-2100
    month: number; // 1-12
}

/**
 * 캘린더 예약 응답
 */
export interface CalendarReservationResponse {
    data: string[]; // ISO Date 배열
}

export type ApiResponseCalendarReservation = ApiResponse<CalendarReservationResponse>;

// =================================================================
// Patient Search (환자 검색)
// =================================================================

/**
 * 환자 검색 요청
 * GET /doctor/patients
 */
export interface PatientSearchRequest {
    date?: ISODate;
    year?: number;
    month?: number;
    day?: number;
    name?: string;
    resultStatus?: string;
    page?: number;  // 0부터 시작
    size?: number;  // 1-100
}

/**
 * 자녀 응답 (환자 정보)
 */
export interface ChildResponse {
    childId: UUID;
    userId: UUID;
    name: string;
    monthlyAge: number;
    birthdate: ISODate;
    gender: string;
    latestExamStatus: string;
}

/**
 * 환자 검색 응답
 */
export interface PatientSearchResponse {
    childResponses: ChildResponse[];
    total: number;
}

export type ApiResponsePatientSearch = ApiResponse<PatientSearchResponse>;
