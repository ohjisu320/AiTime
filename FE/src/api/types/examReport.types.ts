// src/api/types/examReport.types.ts
import type { ApiResponse } from '../types';

// 1. 비디오 타입 상수 정의
export type VideoType =
    | 'POSE_IMITATION'      // 동작 모방
    | 'SPEECH_IMITATION'    // 발화 모방
    | 'NAME_FACING'         // 대면 호명
    | 'NAME_NON_FACING';    // 비대면 호명

// 2. 타임스탬프 상세 타입 정의

// 2-1. 동작 모방 (Task 1) - 부모/아이 구간 분리됨
export interface PoseTimestamp {
    parentStartTime: number;
    parentEndTime: number;
    childStartTime: number | null;  // API에서 null 반환 가능 (아이 미반응 시)
    childEndTime: number | null;    // API에서 null 반환 가능
    trialIndex: number;
}

// 2-2. 발화 모방 (Task 2) & 대면 호명 (Task 3) - 단순 구간
export interface SimpleTimestamp {
    trialStartS: number;
    trialEndS: number;
    trialIndex: number;
}

// 2-3. 비대면 호명 (Task 4) - 자극(Trigger)과 호명(Voice) 구간 분리
export interface NonFacingTimestamp {
    triggerStartS: number;
    triggerEndS: number;
    voiceStartS: number;
    voiceEndS: number;
    trialIndex: number;
}

// 3. 통합 타임스탬프 타입 (Union Type)
export type AnyTimestamp = PoseTimestamp | SimpleTimestamp | NonFacingTimestamp;

// 4. 비디오 프리사인 뷰 응답 (상세 조회용)
export interface VideoPresignView {
    videoId: string;
    videoType: VideoType;
    examId: string;
    bucket: string;
    s3Key: string;
    viewUrl: string;
    expiresAt: string;
    timestamps?: AnyTimestamp[]; // 타임스탬프가 없을 수도 있음 (옵셔널)
}

// 5. 검사 및 비디오 목록 (SessionListPanel용)
export interface ExamVideoListItem {
    examId: string;
    examDate: string;
    examStatus: string;
    videos: {
        videoId: string;
        videoType: VideoType;
    }[];
}

// 7. ADOS 그래프 데이터
export interface AdosGraphs {
    xAxis: string[]; // 날짜 배열 ["2024-01-01", "2024-02-01", ...]
    graphs: {
        graph1: { series: { [key: string]: number[] } }; // Social Affect
        graph2: { series: { [key: string]: number[] } }; // RRB
        graph3: { series: { [key: string]: number[] } }; // Communication
        graph4: { series: { [key: string]: number[] } }; // Interaction
    };
}

// 8. ADOS 상세 점수 데이터
export interface AdosScores {
    total: number;
    socialAffectTotal: number;
    rrbTotal: number;
    [key: string]: number; // a2, b1 등 동적 키 허용
}

export interface AdosDetail {
    adosId?: string;
    examId: string;
    scores: AdosScores;
}

// 6. 초기 리포트 통합 데이터 (대시보드 진입용)
export interface ExamReportInitialData {
    examVideoList: ExamVideoListItem[];
    latestPoseVideo: VideoPresignView | null;  // API 명세 기준 필드명
    adosGraphs: AdosGraphs | null;
    latestAdosDetail: AdosDetail | null;
}

// 9. ADOS 수정 요청 데이터
export type AdosUpdateRequest = Record<string, number>;

// API Responses
export type ApiResponseExamReportInitial = ApiResponse<ExamReportInitialData>;
