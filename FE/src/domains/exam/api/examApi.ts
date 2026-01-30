import api from '@/api/axiosConfig';
import type { ApiResponseExamStart, ExamStartRequest } from '@/api/types/child.types';

/**
 * 검사 시작 API
 * POST /child/{childId}/exam
 */
export const startExam = async (childId: string, data: ExamStartRequest) => {
    const response = await api.post<ApiResponseExamStart>(
        `/child/${childId}/exam`,
        data
    );
    return response.data;
};
