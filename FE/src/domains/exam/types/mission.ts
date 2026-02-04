import type { VideoTask } from '../api/examApi';

export interface Mission extends Omit<VideoTask, 'videoType'> {
    videoType: string;
    title?: string;
    subTitle?: string;
    description?: string;
    variant?: string;
    detail?: any;
    type?: string;
    originalVideoType?: string;
}
