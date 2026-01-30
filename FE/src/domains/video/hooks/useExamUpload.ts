import { useMutation } from '@tanstack/react-query';
import { videoApi } from '../api/videoApi';

interface UploadParams {
  examId: string;
  videoType: string;
  videoBlob: Blob;
  attempts: any[];
}

export const useExamUpload = () => {
  return useMutation({
    mutationFn: async ({ examId, videoType, videoBlob, attempts }: UploadParams) => {
      // 1. URL 발급
      const { videoId, presignedUrl } = await videoApi.getPresignedUrl(examId, videoType);
      // 2. S3 업로드
      await videoApi.uploadToS3(presignedUrl, videoBlob);
      // 3. 서버 상태 완료 처리
      return await videoApi.updateVideoStatus(videoId, attempts);
    }
  });
};