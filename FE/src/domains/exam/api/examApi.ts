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

export interface VideoTask {
    videoType: 'POSE_IMITATION' | 'SPEECH_IMITATION' | 'NAME_FACING' | 'NAME_NON_FACING';
    status: 'EMPTY' | 'UPLOADED' | 'PASS' | 'FAIL';
    videoId: string | null;
}

export interface ExamInfoResponse {
    examId: string;
    under18: boolean;
    status: string;
    videoTasks: VideoTask[];
}

interface ApiResponseExamInfoResponse {
    code: number;
    status: string;
    message: string;
    data: ExamInfoResponse;
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

/**
 * 검사 정보 조회
 * GET /exam/{childId}/examInfo
 */
export const getExamInfo = async (childId: string): Promise<ExamInfoResponse> => {
    console.log(`📤 [GET] 검사 정보 조회: /exam/${childId}/examInfo`);

    const response = await api.get<ApiResponseExamInfoResponse>(
        `/exam/${childId}/examInfo`
    );

    console.log('✅ 검사 정보 응답:', response.data);

    if (response.data.data) {
        const examInfo = response.data.data;

        // examId를 localStorage에 저장
        if (examInfo.examId) {
            localStorage.setItem('examId', examInfo.examId);
            console.log(`✅ examId 저장: ${examInfo.examId}`);
        }

        return examInfo;
    } else {
        throw new Error(response.data.message || '검사 정보 조회 실패');
    }
};
