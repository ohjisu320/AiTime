// API 응답 타입 정의
export interface VideoTask {
    videoType: 'TASK1' | 'TASK2' | 'TASK3' | 'TASK4';
    status: 'UPLOADED' | 'EMPTY' | 'PENDING';
    videoId: string | null;
}

export interface ExamProgressData {
    examId: string;
    under18: boolean;
    status: 'IN_PROGRESS' | 'COMPLETED';
    videoTasks: VideoTask[];
}

export interface ApiResponse<T> {
    status: 'OK' | 'ERROR';
    message: string;
    data: T;
    code: number;
}

// UI에서 사용할 확장된 미션 타입
export interface Mission extends VideoTask {
    title: string;
    subTitle?: string;
    description: string;
    variant: 'pink' | 'amber' | 'emerald' | 'violet';
    detail: {
        steps?: Array<{
            title: string;
            guide?: string;
            script?: string;
        }>;
        words?: string[];
        guideLines?: string[];
    };
    type: string;
}
