// src/features/doctor/api/examReportApi.ts
import api from '@/api/axiosConfig';
import type {
    ExamReportInitialData,
    ExamVideoListItem,
    VideoPresignView,
    AdosGraphs,
    AdosDetail,
} from '@/api/types/examReport.types';

export const examReportApi = {
    /**
     * 0) 환아 검사 리포트 초기 데이터 조회 (통합)
     * GET /api/v1/doctor/{hospitalChildrenId}/exam-reports/initial
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
     * 3) 비디오 상세 (타임스탬프 X, 일반 조회용)
     * GET /api/v1/exam/{examId}/videos/{videoId}
     */
    getVideoPresignView: async (examId: string, videoId: string): Promise<VideoPresignView> => {
        console.log(`📡 [API] 비디오 상세 조회: ${videoId} (examId: ${examId})`);
        const { data } = await api.get<{ code: number; message: string; data: VideoPresignView }>(
            `/exam/${examId}/videos/${videoId}`
        );
        console.log('✅ [API] 비디오 상세 조회 완료');
        return data.data;
    },

    /**
     * 3-1) 비디오 상세 + 타임스탬프 (의료진용)
     * GET /api/v1/exam/{examId}/videos/{videoId}/with-timestamps
     */
    getVideoPresignViewWithTimestamps: async (
        examId: string,
        videoId: string
    ): Promise<VideoPresignView> => {
        console.log(`📡 [API] 비디오(타임스탬프) 조회: ${videoId} (examId: ${examId})`);
        const { data } = await api.get<{ code: number; message: string; data: VideoPresignView }>(
            `/exam/${examId}/videos/${videoId}/with-timestamps`
        );
        console.log('✅ [API] 비디오(타임스탬프) 조회 완료');
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
    updateAdos: async (examId: string, scores: Record<string, number>): Promise<AdosDetail> => {
        console.log(`📡 [API] ADOS 수정: ${examId}`);
        const { data } = await api.put<{ code: number; message: string; data: AdosDetail }>(
            `/doctor/exams/${examId}/ados`,
            scores
        );
        console.log('✅ [API] ADOS 수정 완료');
        return data.data;
    }
};