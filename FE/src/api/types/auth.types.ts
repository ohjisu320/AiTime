/**
 * 인증 관련 API 타입 정의
 * Endpoints: /user/*, /hospital-staff/*, /auth/*
 */

import type { ApiResponse, UUID, ISODateTime, UserRole, StaffRole } from '../types';

// =================================================================
// User Authentication (사용자 인증)
// =================================================================

/**
 * 사용자 로그인 요청
 * POST /user/login
 */
export interface UserLoginRequest {
    loginId: string;
    password: string;
}

/**
 * 사용자 정보 DTO
 */
export interface UserInfoDTO {
    userId: UUID;
    name: string;
    userRole: UserRole;
}

/**
 * 사용자 로그인 응답
 */
export interface UserLoginResponse {
    accessToken: string;
    userInfoDTO: UserInfoDTO;
}

export type ApiResponseUserLogin = ApiResponse<UserLoginResponse>;

/**
 * 사용자 회원가입 요청
 * POST /user/join
 */
export interface UserJoinRequest {
    loginId: string;
    password: string;
    name: string;
    phoneNumber: string;
    privacyAgreed?: boolean;
}

/**
 * 사용자 회원가입 응답
 */
export interface UserJoinResponse {
    userId: UUID;
    loginId: string;
    name: string;
}

export type ApiResponseUserJoin = ApiResponse<UserJoinResponse>;

/**
 * 사용자 정보 조회 응답
 * GET /user/me
 */
export interface UserMeResponse {
    userId: UUID;
    name: string;
    phoneNumber: string;
    loginId: string;
}

export type ApiResponseUserMe = ApiResponse<UserMeResponse>;

/**
 * 사용자 정보 수정 요청
 * PATCH /user/me
 */
export interface UserUpdateRequest {
    name: string;
    phoneNumber: string;
}

/**
 * 사용자 정보 수정 응답
 */
export interface UserUpdateResponse {
    name: string;
    phoneNumber: string;
    updatedAt: ISODateTime;
}

export type ApiResponseUserUpdate = ApiResponse<UserUpdateResponse>;

/**
 * 비밀번호 재설정 요청
 * PATCH /user/password
 */
export interface PasswordResetRequest {
    userId: UUID;
    password: string;
}

/**
 * 비밀번호 재설정 응답
 */
export interface PasswordResetResponse {
    userId: UUID;
    updatedAt: ISODateTime;
}

export type ApiResponsePasswordReset = ApiResponse<PasswordResetResponse>;

/**
 * 사용자 본인 확인 응답
 * GET /user/verify-identity
 */
export interface UserIdentityResponse {
    isVerified: boolean;
    userId: UUID;
}

export type ApiResponseUserIdentity = ApiResponse<UserIdentityResponse>;

/**
 * 아이디 찾기 응답
 * GET /user/get-id
 */
export interface IdFindResponse {
    loginId: string;
    createdAt: ISODateTime;
}

export type ApiResponseIdFind = ApiResponse<IdFindResponse>;

/**
 * 아이디 중복 확인 응답
 * GET /user/duplicate-id
 */
export interface IdDuplicateResponse {
    isDuplicate: boolean;
}

export type ApiResponseIdDuplicate = ApiResponse<IdDuplicateResponse>;

// =================================================================
// Hospital Staff Authentication (병원 직원 인증)
// =================================================================

/**
 * 병원 직원 로그인 요청
 * POST /hospital-staff/login
 */
export interface HospitalStaffLoginRequest {
    loginId: string;
    password: string;
}

/**
 * 병원 직원 정보 DTO
 */
export interface HospitalStaffInfoDTO {
    hospitalStaffId: UUID;
    name: string;
    staffRole: StaffRole;
}

/**
 * 병원 직원 로그인 응답
 */
export interface HospitalStaffLoginResponse {
    accessToken: string;
    hospitalStaffInfoDTO: HospitalStaffInfoDTO;
}

export type ApiResponseHospitalStaffLogin = ApiResponse<HospitalStaffLoginResponse>;

// =================================================================
// Phone Verification (전화번호 인증)
// =================================================================

/**
 * 인증번호 발송 요청
 * POST /auth/phone/verification
 */
export interface PhoneVerificationRequest {
    phoneNumber: string; // 010으로 시작하는 7-8자리
}

/**
 * 인증번호 발송 응답
 */
export interface PhoneVerificationResponse {
    phoneNumber: string;
    expiredAt: ISODateTime;
}

export type ApiResponsePhoneVerification = ApiResponse<PhoneVerificationResponse>;

/**
 * 인증번호 확인 요청
 * POST /auth/phone/verify
 */
export interface PhoneVerifyRequest {
    phoneNumber: string;
    verificationCode: string;
}

/**
 * 인증번호 확인 응답
 */
export type ApiResponsePhoneVerify = ApiResponse<{ [key: string]: boolean }>;
