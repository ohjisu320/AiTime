import { describe, it, expect, vi, beforeEach } from 'vitest';
import axios from 'axios';
import { videoApi } from './videoApi';
import api from '@/api/axiosConfig';

// Mock dependencies
vi.mock('axios');
vi.mock('@/api/axiosConfig', () => ({
    default: {
        post: vi.fn(),
        patch: vi.fn(),
    },
}));

describe('videoApi', () => {
    beforeEach(() => {
        vi.clearAllMocks();
    });

    describe('getPresignedUrl', () => {
        it('should call api.post with correct parameters', async () => {
            const mockResponse = {
                data: {
                    data: {
                        videoId: 'v1',
                        uploadUrl: 'http://minio/upload',
                        s3Key: 'key',
                        requiredHeaders: { 'Content-Type': 'video/mp4' },
                    },
                },
            };

            (api.post as any).mockResolvedValue(mockResponse);

            const result = await videoApi.getPresignedUrl('exam1', 'POSE_IMITATION', 'video/mp4', 1000);

            expect(api.post).toHaveBeenCalledWith('/exam/exam1/videos/presign-upload', {
                videoType: 'POSE_IMITATION',
                contentType: 'video/mp4',
                contentLength: 1000,
            });
            expect(result).toEqual(mockResponse.data.data);
        });
    });

    describe('uploadToMinio', () => {
        it('should call axios.put with correct configuration for MinIO', async () => {
            const uploadUrl = 'http://minio/upload';
            const file = new Blob(['video data'], { type: 'video/mp4' });
            const requiredHeaders = { 'Content-Type': 'video/mp4' };

            // Mock axios.put to resolve successfully
            (axios.put as any).mockResolvedValue({ status: 200 });

            await videoApi.uploadToMinio(uploadUrl, file, requiredHeaders);

            expect(axios.put).toHaveBeenCalledTimes(1);
            const [calledUrl, calledFile, config] = (axios.put as any).mock.calls[0];

            expect(calledUrl).toBe(uploadUrl);
            expect(calledFile).toBe(file);

            // Verify Critical MinIO Configurations
            expect(config.responseType).toBe('text');
            expect(config.headers['Content-Type']).toBe('video/mp4');

            // Verify transformResponse
            const transformRespFn = config.transformResponse[0];
            const testData = "some data";
            expect(transformRespFn(testData)).toBe(testData); // Should return data as-is

            // Verify transformRequest (Authorization header removal)
            const transformReqFn = config.transformRequest[0];
            const headers = { common: { Authorization: 'Bearer token' }, Authorization: 'Bearer token' };
            transformReqFn(null, headers);
            expect(headers.Authorization).toBeUndefined();
            expect(headers.common['Authorization']).toBeUndefined();
        });
    });

    describe('updateVideoStatus', () => {
        it('should call api.post with correct endpoint containing examId and videoId and s3Key', async () => {
            const examId = 'exam123';
            const videoId = 'video456';
            const s3Key = 'video/key.mp4';

            (api.post as any).mockResolvedValue({ data: { data: 'success' } });

            await videoApi.updateVideoStatus(examId, videoId, s3Key);

            expect(api.post).toHaveBeenCalledWith(
                `/exam/${examId}/videos/${videoId}/complete`,
                { s3Key }
            );
        });
    });
});
