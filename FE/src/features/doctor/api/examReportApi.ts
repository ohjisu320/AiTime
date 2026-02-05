// src/features/doctor/api/examReportApi.ts
import api from '@/api/axiosConfig';
import type {
    ApiResponseExamReportInitial,
    ApiResponseExamVideoList,
    ApiResponseVideoPresignView,
    ApiResponseAdosGraphs,
    ApiResponseAdosDetail,
    ExamReportInitialData,
    ExamVideoListItem,
    VideoPresignView,
    AdosGraphs,
    AdosDetail,
    AdosUpdateRequest,
} from '@/api/types/examReport.types';

/**
 * 환아 검사 리포트 API
 */
export const examReportApi = {
    /**
     * 0) 환아 검사 리포트 초기 데이터 조회 (통합)
     * GET /doctor/{hospitalChildrenId}/exam-reports/initial
     */
    getExamReportsInitial: async (
        hospitalChildrenId: string,
        expiresInSec: number = 300
    ): Promise<ExamReportInitialData> => {
        console.log(`📡 [API] 초기 데이터 조회: ${hospitalChildrenId}`);

        const { data } = await api.get<ApiResponseExamReportInitial>(
            `/doctor/${hospitalChildrenId}/exam-reports/initial`,
            { params: { expiresInSec } }
        );

        console.log('✅ 초기 데이터 조회 완료:', data.data);
        return data.data;
    },

    /**
     * 2) 검사별 비디오 목록 조회
     * GET /doctor/{hospitalChildrenId}/exams
     */
    getExamList: async (hospitalChildrenId: string): Promise<ExamVideoListItem[]> => {
        console.log(`📡 [API] 검사 목록 조회: ${hospitalChildrenId}`);

        const { data } = await api.get<ApiResponseExamVideoList>(
            `/doctor/${hospitalChildrenId}/exams`
        );

        console.log('✅ 검사 목록 조회 완료:', data.data);
        return data.data;
    },

    /**
     * 3) 비디오 상세 + 타임스탬프 조회
     * GET /doctor/videos/{videoId}/presign-view
     */
    getVideoPresignView: async (videoId: string): Promise<VideoPresignView> => {
        console.log(`📡 [API] 비디오 상세 조회: ${videoId}`);

        const { data } = await api.get<ApiResponseVideoPresignView>(
            `/doctor/videos/${videoId}/presign-view`
        );

        console.log('✅ 비디오 상세 조회 완료:', data.data);
        return data.data;
    },

    /**
     * 4) 날짜별 ADOS 시계열 조회 (4개 그래프)
     * GET /doctor/{hospitalChildrenId}/exam-reports/ados-graphs
     */
    getAdosGraphs: async (hospitalChildrenId: string): Promise<AdosGraphs | null> => {
        console.log(`📡 [API] ADOS 그래프 조회: ${hospitalChildrenId}`);

        const { data } = await api.get<ApiResponseAdosGraphs>(
            `/doctor/${hospitalChildrenId}/exam-reports/ados-graphs`
        );

        console.log('✅ ADOS 그래프 조회 완료:', data.data);
        return data.data;
    },

    /**
     * 5) 검사(Exam) 기준 ADOS 상세 조회
     * GET /doctor/exams/{examId}/ados
     */
    getAdosDetail: async (examId: string): Promise<AdosDetail | null> => {
        console.log(`📡 [API] ADOS 상세 조회: ${examId}`);

        const { data } = await api.get<ApiResponseAdosDetail>(
            `/doctor/exams/${examId}/ados`
        );

        console.log('✅ ADOS 상세 조회 완료:', data.data);
        return data.data;
    },

    /**
     * 6) 검사(Exam) 기준 ADOS 수정
     * PUT /doctor/exams/{examId}/ados
     */
    updateAdos: async (examId: string, scores: AdosUpdateRequest): Promise<AdosDetail> => {
        console.log(`📡 [API] ADOS 수정: ${examId}`, scores);

        const { data } = await api.put<ApiResponseAdosDetail>(
            `/doctor/exams/${examId}/ados`,
            scores
        );

        console.log('✅ ADOS 수정 완료:', data.data);
        return data.data;
    },
};
