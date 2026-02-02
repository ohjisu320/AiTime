import api from '@/api/axiosConfig';

// ==================== Types ====================

export interface ExamStartRequest {
    videoConsent: boolean;
}

export interface ExamStartResponse {
    examId: string;
}

export interface ApiResponseExamStartResponse {
    code: number;
    status: string;
    message: string;
    data: ExamStartResponse;
}

// ==================== API Functions ====================

/**
 * 검사 시작 - examId 발급
 * POST /child/{childId}/exam
 */
export const startExam = async (childId: string): Promise<string> => {
    const requestBody: ExamStartRequest = {
        videoConsent: true
    };

    console.log(`📤 [POST] 검사 시작 요청: /child/${childId}/exam`);

    const response = await api.post<ApiResponseExamStartResponse>(
        `/child/${childId}/exam`,
        requestBody
    );

    console.log('✅ 검사 시작 응답:', response.data);

    if (response.data.data && response.data.data.examId) {
        const examId = response.data.data.examId;
        console.log(`✅ examId 발급: ${examId}`);
        return examId;
    } else {
        throw new Error(response.data.message || '검사 시작 실패');
    }
};
