/**
 * 자녀 관련 API 타입 정의
 * Endpoints: /child/*
 */

import type { ApiResponse, UUID, ISODate, Gender, ChildStatus, HospitalLinkStatus } from '../types';

// =================================================================
// Child Management (자녀 관리)
// =================================================================

/**
 * 자녀 등록 요청
 * POST /child
 */
export interface ChildCreateRequest {
    name: string;
    birthdate: ISODate;
    gender: Gender;
}

/**
 * 자녀 정보 응답
 */
export interface ChildInfoResponse {
    childId: UUID;
    name: string;
    months: number;
    gender: Gender;
}

export type ApiResponseChildInfo = ApiResponse<ChildInfoResponse>;

/**
 * 자녀 목록 조회 응답
 * GET /child
 */
export type ApiResponseChildList = ApiResponse<ChildInfoResponse[]>;

/**
 * 자녀 삭제 응답
 * DELETE /child/{childId}
 */
export interface ChildDeleteResponse {
    childId: UUID;
    status: ChildStatus;
}

export type ApiResponseChildDelete = ApiResponse<ChildDeleteResponse>;

// =================================================================
// Child Home (자녀 홈 화면)
// =================================================================

/**
 * 병원 정보 DTO
 */
export interface HospitalInfoDTO {
    hospitalId: string;
    name: string;
}

/**
 * 자녀 홈 화면 응답
 * GET /child/{childId}
 */
export interface ChildHomeResponse {
    childId: UUID;
    name: string;
    gender: Gender;
    examStatus: 'NEED_HOSPITAL' | 'AVAILABLE' | 'AVAILABLE_EXPIRED' | 'IN_PROGRESS' | 'COOLDOWN' | 'COOLDOWN_BEFORE';
    examProgress: number;
    examStartedAt?: ISODate;
    nextEligibleAt?: ISODate;
    draftExpiresAt?: string; // ISO DateTime
    linkedHospitals: HospitalInfoDTO[];
}

export type ApiResponseChildHome = ApiResponse<ChildHomeResponse>;

// =================================================================
// Hospital Link (병원 연결)
// =================================================================

/**
 * 초대코드 등록 요청
 * POST /child/{childId}/hospital-link
 */
export interface ChildHospitalLinkRequest {
    inviteCode: string;
}

/**
 * 병원 응답 DTO
 */
export interface HospitalResponseDto {
    hospitalId: UUID;
    name: string;
    address: string;
    phoneNumber: string;
    linkStatus: HospitalLinkStatus;
}

/**
 * 자녀 병원 목록 응답
 * GET /child/{childId}/hospital-list
 */
export interface ChildHospitalListResponse {
    data: HospitalResponseDto[];
}

export type ApiResponseChildHospitalList = ApiResponse<ChildHospitalListResponse>;

// =================================================================
// Exam (검사)
// =================================================================

/**
 * 검사 시작 요청
 * POST /child/{childId}/exam
 */
export interface ExamStartRequest {
    videoConsent: boolean;
}

/**
 * 검사 시작 응답
 */
export interface ExamStartResponse {
    examId: UUID;
    childId: UUID;
    status: 'IN_PROGRESS' | 'COMPLETED';
}

export type ApiResponseExamStart = ApiResponse<ExamStartResponse>;
