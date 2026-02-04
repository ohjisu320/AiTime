/**
 * 공통 API 타입 정의
 * OpenAPI 3.1.0 스펙 기반
 * Base URL: http://70.12.246.95:8080/api/v1
 */

// =================================================================
// 공통 응답 구조 (Common Response Structure)
// =================================================================

/**
 * HTTP 상태 코드 Enum
 */
export type HttpStatus =
    | '100 CONTINUE'
    | '101 SWITCHING_PROTOCOLS'
    | '102 PROCESSING'
    | '103 EARLY_HINTS'
    | '200 OK'
    | '201 CREATED'
    | '202 ACCEPTED'
    | '203 NON_AUTHORITATIVE_INFORMATION'
    | '204 NO_CONTENT'
    | '205 RESET_CONTENT'
    | '206 PARTIAL_CONTENT'
    | '207 MULTI_STATUS'
    | '208 ALREADY_REPORTED'
    | '226 IM_USED'
    | '300 MULTIPLE_CHOICES'
    | '301 MOVED_PERMANENTLY'
    | '302 FOUND'
    | '303 SEE_OTHER'
    | '304 NOT_MODIFIED'
    | '307 TEMPORARY_REDIRECT'
    | '308 PERMANENT_REDIRECT'
    | '400 BAD_REQUEST'
    | '401 UNAUTHORIZED'
    | '402 PAYMENT_REQUIRED'
    | '403 FORBIDDEN'
    | '404 NOT_FOUND'
    | '405 METHOD_NOT_ALLOWED'
    | '406 NOT_ACCEPTABLE'
    | '407 PROXY_AUTHENTICATION_REQUIRED'
    | '408 REQUEST_TIMEOUT'
    | '409 CONFLICT'
    | '410 GONE'
    | '411 LENGTH_REQUIRED'
    | '412 PRECONDITION_FAILED'
    | '413 CONTENT_TOO_LARGE'
    | '414 URI_TOO_LONG'
    | '415 UNSUPPORTED_MEDIA_TYPE'
    | '416 REQUESTED_RANGE_NOT_SATISFIABLE'
    | '417 EXPECTATION_FAILED'
    | '418 I_AM_A_TEAPOT'
    | '421 MISDIRECTED_REQUEST'
    | '422 UNPROCESSABLE_CONTENT'
    | '423 LOCKED'
    | '424 FAILED_DEPENDENCY'
    | '425 TOO_EARLY'
    | '426 UPGRADE_REQUIRED'
    | '428 PRECONDITION_REQUIRED'
    | '429 TOO_MANY_REQUESTS'
    | '431 REQUEST_HEADER_FIELDS_TOO_LARGE'
    | '451 UNAVAILABLE_FOR_LEGAL_REASONS'
    | '500 INTERNAL_SERVER_ERROR'
    | '501 NOT_IMPLEMENTED'
    | '502 BAD_GATEWAY'
    | '503 SERVICE_UNAVAILABLE'
    | '504 GATEWAY_TIMEOUT'
    | '505 HTTP_VERSION_NOT_SUPPORTED'
    | '506 VARIANT_ALSO_NEGOTIATES'
    | '507 INSUFFICIENT_STORAGE'
    | '508 LOOP_DETECTED'
    | '509 BANDWIDTH_LIMIT_EXCEEDED'
    | '510 NOT_EXTENDED'
    | '511 NETWORK_AUTHENTICATION_REQUIRED';

/**
 * 기본 API 응답 구조
 */
export interface ApiResponse<T = unknown> {
    code: number;
    status: HttpStatus;
    message: string;
    data: T;
}

/**
 * Void 응답 (데이터 없음)
 */
export type ApiResponseVoid = ApiResponse<void>;

/**
 * String 응답
 */
export type ApiResponseString = ApiResponse<string>;

/**
 * Object 응답 (타입 미지정)
 */
export type ApiResponseObject = ApiResponse<object>;

// =================================================================
// 공통 Enum 타입 (Common Enums)
// =================================================================

/**
 * 성별
 */
export const Gender = {
    MALE: 'MALE',
    FEMALE: 'FEMALE',
} as const;
export type Gender = typeof Gender[keyof typeof Gender];

/**
 * 사용자 역할
 */
export const UserRole = {
    USER: 'USER',
    ADMIN: 'ADMIN',
} as const;
export type UserRole = typeof UserRole[keyof typeof UserRole];

/**
 * 병원 직원 역할
 */
export const StaffRole = {
    DESK: 'DESK',
    DOCTOR: 'DOCTOR',
} as const;
export type StaffRole = typeof StaffRole[keyof typeof StaffRole];

/**
 * 초대 코드 상태
 */
export const InviteCodeStatus = {
    ISSUED: 'ISSUED',
    REGISTERED: 'REGISTERED',
    REVOKED: 'REVOKED',
} as const;
export type InviteCodeStatus = typeof InviteCodeStatus[keyof typeof InviteCodeStatus];

/**
 * 검사 상태
 */
export const ExamStatus = {
    IN_PROGRESS: 'IN_PROGRESS',
    COMPLETED: 'COMPLETED',
} as const;
export type ExamStatus = typeof ExamStatus[keyof typeof ExamStatus];

/**
 * 자녀 상태
 */
export const ChildStatus = {
    ACTIVE: 'ACTIVE',
    DELETED: 'DELETED',
} as const;
export type ChildStatus = typeof ChildStatus[keyof typeof ChildStatus];

/**
 * 병원 연결 상태
 */
export const HospitalLinkStatus = {
    ACTIVE: 'ACTIVE',
    INACTIVE: 'INACTIVE',
} as const;
export type HospitalLinkStatus = typeof HospitalLinkStatus[keyof typeof HospitalLinkStatus];

/**
 * 자녀 대시보드 상태 (프론트엔드 전용)
 */
export const ChildDashboardStatus = {
    NEED_HOSPITAL: 'NEED_HOSPITAL',           // 병원 연결 필요
    AVAILABLE: 'AVAILABLE',                   // 새 검사 가능
    AVAILABLE_EXPIRED: 'AVAILABLE_EXPIRED',   // 검사 가능 (이전 임시저장 만료됨)
    IN_PROGRESS: 'IN_PROGRESS',               // 검사 진행 중 (이어하기)
    COOLDOWN: 'COOLDOWN',                     // 쿨타임 (다음 검사 대기)
    COOLDOWN_BEFORE: 'COOLDOWN_BEFORE',       // 쿨타임 중 병원 연동됨
    WAITING: 'WAITING',                       // 대기 중
} as const;
export type ChildDashboardStatus = typeof ChildDashboardStatus[keyof typeof ChildDashboardStatus];

// =================================================================
// 공통 에러 타입 (Error Types)
// =================================================================

/**
 * API 에러 응답
 */
export interface ApiError {
    code: number;
    status: HttpStatus;
    message: string;
    data?: unknown;
}

/**
 * 네트워크 에러
 */
export interface NetworkError {
    message: string;
    code?: string;
    config?: unknown;
}

// =================================================================
// 페이지네이션 (Pagination)
// =================================================================

/**
 * 페이지네이션 요청 파라미터
 */
export interface PaginationRequest {
    page?: number;  // 0부터 시작
    size?: number;  // 1-100
}

/**
 * 페이지네이션 응답
 */
export interface PaginationResponse<T> {
    content: T[];
    total: number;
    page?: number;
    size?: number;
    totalPages?: number;
}

// =================================================================
// 날짜/시간 타입 (Date/Time Types)
// =================================================================

/**
 * ISO 8601 날짜 문자열 (YYYY-MM-DD)
 */
export type ISODate = string;

/**
 * ISO 8601 날짜-시간 문자열 (YYYY-MM-DDTHH:mm:ss)
 */
export type ISODateTime = string;

// =================================================================
// UUID 타입
// =================================================================

/**
 * UUID v4 문자열
 */
export type UUID = string;
