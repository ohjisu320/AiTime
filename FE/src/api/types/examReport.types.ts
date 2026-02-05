/**
 * 환아 검사 리포트 API 타입 정의
 * Endpoints: /doctor/{hospitalChildrenId}/exam-reports/*, /doctor/exams/*, /doctor/videos/*
 */

import type { ApiResponse, UUID, ISODate, ISODateTime, ExamStatus } from '../types';

// =================================================================
// Video Types (비디오 관련 타입)
// =================================================================

/**
 * 비디오 유형
 */
export const VideoType = {
    POSE_IMITATION: 'POSE_IMITATION',
    SPEECH_IMITATION: 'SPEECH_IMITATION',
    NAME_FACING: 'NAME_FACING',
    NAME_NON_FACING: 'NAME_NON_FACING',
} as const;
export type VideoType = typeof VideoType[keyof typeof VideoType];

/**
 * 비디오 아이템 (목록용)
 */
export interface VideoItem {
    videoId: UUID;
    videoType: VideoType;
}

/**
 * 타임스탬프 (이벤트 구간)
 */
export interface Timestamp {
    startS: number;
    endS: number;
    trialIndex: number;
}

/**
 * 비디오 상세 정보 (presign-view 응답)
 */
export interface VideoPresignView {
    videoId: UUID;
    videoType: VideoType;
    examId: UUID;
    bucket: string;
    s3Key: string;
    viewUrl: string;
    expiresAt: ISODateTime;
    timestamps: Timestamp[];
}

// =================================================================
// Exam Types (검사 관련 타입)
// =================================================================

/**
 * 검사별 비디오 목록 아이템
 */
export interface ExamVideoListItem {
    examId: UUID;
    examDate: ISODate;
    examStatus: ExamStatus;
    videos: VideoItem[];
}

// =================================================================
// ADOS Types (ADOS 관련 타입)
// =================================================================

/**
 * ADOS 그래프 series 데이터
 * key: ADOS 항목 코드 (소문자), value: 점수 배열
 */
export interface AdosGraphSeries {
    [key: string]: number[];
}

/**
 * 개별 그래프 데이터
 */
export interface AdosGraph {
    series: AdosGraphSeries;
}

/**
 * ADOS 그래프 전체 데이터
 */
export interface AdosGraphs {
    xAxis: ISODate[];
    graphs: {
        graph1: AdosGraph;
        graph2: AdosGraph;
        graph3: AdosGraph;
        graph4: AdosGraph;
    };
}

/**
 * ADOS 점수 (동적 키)
 * 21개월 미만: a2, a8, b1, b4, b5, b6, b12, b13, b14, b15, a3, d1, d2, d5
 * 21개월 이상: a7, b1, b4, b5, b7, b8, b9, b13, b15, b16b, b18, d1, d2, d5
 * 공통: socialAffectTotal, rrbTotal, total
 */
export interface AdosScores {
    // 21개월 미만 전용
    a2?: number;
    a8?: number;
    b12?: number;
    b14?: number;

    // 21개월 이상 전용
    a7?: number;
    b7?: number;
    b8?: number;
    b9?: number;
    b16b?: number;
    b18?: number;

    // 공통 항목
    b1?: number;
    b4?: number;
    b5?: number;
    b6?: number;
    b13?: number;
    b15?: number;

    // RRB 항목
    a3?: number;
    d1?: number;
    d2?: number;
    d5?: number;

    // 합계
    socialAffectTotal: number;
    rrbTotal: number;
    total: number;

    // 추가 동적 키 허용
    [key: string]: number | undefined;
}

/**
 * ADOS 상세 정보
 */
export interface AdosDetail {
    adosId: UUID;
    examId: UUID;
    scores: AdosScores;
}

/**
 * ADOS 수정 요청 (21개월 미만)
 */
export interface AdosUpdateRequestUnder21 {
    a2?: number;
    a8?: number;
    b1?: number;
    b4?: number;
    b5?: number;
    b6?: number;
    b12?: number;
    b13?: number;
    b14?: number;
    b15?: number;
    a3?: number;
    d1?: number;
    d2?: number;
    d5?: number;
}

/**
 * ADOS 수정 요청 (21개월 이상)
 */
export interface AdosUpdateRequestOver21 {
    a7?: number;
    b1?: number;
    b4?: number;
    b5?: number;
    b7?: number;
    b8?: number;
    b9?: number;
    b13?: number;
    b15?: number;
    b16b?: number;
    b18?: number;
    d1?: number;
    d2?: number;
    d5?: number;
}

/**
 * ADOS 수정 요청 (통합)
 */
export type AdosUpdateRequest = AdosUpdateRequestUnder21 | AdosUpdateRequestOver21;

// =================================================================
// Initial Data Types (초기 데이터 통합 응답)
// =================================================================

/**
 * 환아 검사 리포트 초기 데이터 (통합 응답)
 * GET /doctor/{hospitalChildrenId}/exam-reports/initial
 */
export interface ExamReportInitialData {
    examVideoList: ExamVideoListItem[];
    latestPoseImitationVideo: VideoPresignView | null;
    adosGraphs: AdosGraphs | null;
    latestAdosDetail: AdosDetail | null;
}

// =================================================================
// API Response Types
// =================================================================

export type ApiResponseExamReportInitial = ApiResponse<ExamReportInitialData>;
export type ApiResponseExamVideoList = ApiResponse<ExamVideoListItem[]>;
export type ApiResponseVideoPresignView = ApiResponse<VideoPresignView>;
export type ApiResponseAdosGraphs = ApiResponse<AdosGraphs>;
export type ApiResponseAdosDetail = ApiResponse<AdosDetail>;
