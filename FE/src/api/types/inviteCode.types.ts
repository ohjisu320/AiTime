/**
 * 초대코드 관련 API 타입 정의
 * Endpoints: /invite-code/*
 */

import type { ApiResponse, UUID, ISODate, ISODateTime, InviteCodeStatus } from '../types';

// =================================================================
// Invite Code Management (초대코드 관리)
// =================================================================

/**
 * 초대코드 생성 요청
 * POST /invite-code
 */
export interface InviteCodeRequest {
    childName: string;
    childBirthdate: ISODate;
    parentPhone: string;
    scheduledAt: ISODateTime;
    doctorId?: UUID;
}

/**
 * 초대코드 응답
 */
export interface InviteCodeResponse {
    inviteCodeId: UUID;
    inviteCode: string;
    childName: string;
    parentPhone: string;
    status: InviteCodeStatus;
    createdAt: ISODateTime;
}

export type ApiResponseInviteCode = ApiResponse<InviteCodeResponse>;

/**
 * 초대코드 상태 조회 응답
 * GET /invite-code/{inviteCodeId}/status
 */
export interface InviteCodeStatusResponse {
    inviteCodeId: UUID;
    status: InviteCodeStatus;
    childName: string;
}

export type ApiResponseInviteCodeStatus = ApiResponse<InviteCodeStatusResponse>;

/**
 * 초대코드 취소 응답
 * DELETE /invite-code/{inviteCodeId}
 */
export interface InviteCodeRevokeResponse {
    inviteCodeId: UUID;
    status: InviteCodeStatus;
    updatedAt: ISODateTime;
}

export type ApiResponseInviteCodeRevoke = ApiResponse<InviteCodeRevokeResponse>;

// =================================================================
// Unregistered Patients (미등록 환자)
// =================================================================

/**
 * 미등록 환자 응답
 * GET /invite-code/patients
 */
export interface UnregisteredPatientResponse {
    inviteCodeId: UUID;
    inviteCode: string;
    childName: string;
    childMonths: number;
    parentPhone: string;
    scheduledAt: ISODateTime;
    status: InviteCodeStatus;
}

export type ApiResponseUnregisteredPatients = ApiResponse<UnregisteredPatientResponse[]>;

/**
 * 예약 캘린더 응답
 * GET /invite-code/calendar
 */
export type ApiResponseCalendar = ApiResponse<ISODate[]>;
