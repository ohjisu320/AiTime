import type { VideoTask } from '../api/examApi';

export interface Mission extends VideoTask {
    title?: string;
    subTitle?: string;
    description?: string;
    variant?: string;
    detail?: any;
    type?: string;
    originalVideoType?: string;
}
