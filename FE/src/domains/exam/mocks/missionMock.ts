import type { ApiResponse, ExamProgressData } from '../types/mission';

export const MOCK_EXAM_PROGRESS: ExamProgressData = {
    examId: "mock-exam-id-12345",
    under18: true, // 12-17 months
    status: "IN_PROGRESS",
    videoTasks: [
        { videoType: "TASK1", status: "UPLOADED", videoId: "v1_mock" },
        { videoType: "TASK2", status: "UPLOADED", videoId: "v2_mock" },
        { videoType: "TASK3", status: "EMPTY", videoId: null },
        { videoType: "TASK4", status: "EMPTY", videoId: null }
    ]
};

export const getMockExamProgress = (): ApiResponse<ExamProgressData> => {
    return {
        status: "OK",
        message: "검사 진행도 조회가 완료되었습니다. (MOCK)",
        data: MOCK_EXAM_PROGRESS,
        code: 200
    };
};
