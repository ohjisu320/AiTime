// src/features/doctor/api/examReportApi.ts
/**
 * 환아 검사 리포트 API
 * 명세서 기준 구현 (2026-02-05)
 */
import api from '@/api/axiosConfig';
import type {
    ExamReportInitialData,
    ExamVideoListItem,
    VideoPresignView,
    AdosGraphs,
    AdosDetail,
    AdosUpdateRequest,
} from '@/api/types/examReport.types';

export const examReportApi = {
    /**
     * 0) 환아 검사 리포트 초기 데이터 조회 (통합)
     * GET /api/v1/doctor/{hospitalChildrenId}/exam-reports/initial
     * 
     * 포함 데이터:
     * 1. examVideoList - 환아별 검사 목록(검사별 비디오 목록)
     * 2. latestPoseImitationVideo - 최신 POSE_IMITATION 비디오 presign-view + timestamps
     * 3. adosGraphs - 날짜별 ADOS 시계열(4개 그래프)
     * 4. latestAdosDetail - 최신 exam 기준 ADOS 상세
     */
    getExamReportsInitial: async (
        hospitalChildrenId: string,
        expiresInSec: number = 300
    ): Promise<ExamReportInitialData> => {
        console.log(`📡 [API] 초기 데이터 조회: ${hospitalChildrenId}`);
        const { data } = await api.get<{ code: number; message: string; data: ExamReportInitialData }>(
            `/doctor/${hospitalChildrenId}/exam-reports/initial`,
            { params: { expiresInSec } }
        );
        console.log('✅ [API] 초기 데이터 조회 완료');
        return data.data;
    },

    /**
     * 2) 검사별 비디오 목록 조회
     * GET /api/v1/doctor/{hospitalChildrenId}/exams
     */
    getExamList: async (hospitalChildrenId: string): Promise<ExamVideoListItem[]> => {
        console.log(`📡 [API] 검사 목록 조회: ${hospitalChildrenId}`);
        const { data } = await api.get<{ code: number; message: string; data: ExamVideoListItem[] }>(
            `/doctor/${hospitalChildrenId}/exams`
        );
        console.log(`✅ [API] 검사 목록 조회 완료: ${data.data.length}건`);
        return data.data;
    },

    /**
     * 3) 비디오 상세 + 타임스탬프 조회
     * GET /api/v1/doctor/videos/{videoId}/presign-view
     */
    getVideoPresignView: async (videoId: string): Promise<VideoPresignView> => {
        console.log(`📡 [API] 비디오 상세 조회: ${videoId}`);
        const { data } = await api.get<{ code: number; message: string; data: VideoPresignView }>(
            `/doctor/videos/${videoId}/presign-view`
        );
        console.log('✅ [API] 비디오 상세 조회 완료');
        return data.data;
    },

    /**
     * 4) 날짜별 ADOS 시계열 조회 (4개 그래프)
     * GET /api/v1/doctor/{hospitalChildrenId}/exam-reports/ados-graphs
     */
    getAdosGraphs: async (hospitalChildrenId: string): Promise<AdosGraphs | null> => {
        console.log(`📡 [API] ADOS 그래프 조회: ${hospitalChildrenId}`);
        const { data } = await api.get<{ code: number; message: string; data: AdosGraphs }>(
            `/doctor/${hospitalChildrenId}/exam-reports/ados-graphs`
        );
        console.log('✅ [API] ADOS 그래프 조회 완료');
        return data.data;
    },

    /**
     * 5) 검사(Exam) 기준 ADOS 상세 조회
     * GET /api/v1/doctor/exams/{examId}/ados
     */
    getAdosDetail: async (examId: string): Promise<AdosDetail | null> => {
        console.log(`📡 [API] ADOS 상세 조회: ${examId}`);
        const { data } = await api.get<{ code: number; message: string; data: AdosDetail }>(
            `/doctor/exams/${examId}/ados`
        );
        console.log('✅ [API] ADOS 상세 조회 완료');
        return data.data;
    },

    /**
     * 6) 검사(Exam) 기준 ADOS 수정
     * PUT /api/v1/doctor/exams/{examId}/ados
     */
    updateAdos: async (examId: string, scores: AdosUpdateRequest): Promise<AdosDetail> => {
        console.log(`📡 [API] ADOS 수정: ${examId}`);
        const { data } = await api.put<{ code: number; message: string; data: AdosDetail }>(
            `/doctor/exams/${examId}/ados`,
            scores
        );
        console.log('✅ [API] ADOS 수정 완료');
        return data.data;
    },
};