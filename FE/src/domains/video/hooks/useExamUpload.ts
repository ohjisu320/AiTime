import { useMutation } from '@tanstack/react-query';
import { videoApi, type VideoType } from '../api/videoApi';

interface UploadParams {
  examId: string;
  videoType: VideoType;
  videoBlob: Blob;
  onProgress?: (progress: number) => void;  // ✅ 진행률 콜백 옵션
}

// ✅ 재시도 헬퍼 함수
const sleep = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

const retryWithDelay = async <T,>(
  fn: () => Promise<T>,
  retries: number = 3,
  delay: number = 1000
): Promise<T> => {
  try {
    return await fn();
  } catch (error) {
    if (retries === 0) {
      throw error;
    }
    console.warn(`⚠️ 업로드 실패, ${retries}번 재시도 남음. ${delay}ms 후 재시도...`);
    await sleep(delay);
    return retryWithDelay(fn, retries - 1, delay);
  }
};

export const useExamUpload = () => {
  return useMutation({
    mutationFn: async ({ examId, videoType, videoBlob, onProgress }: UploadParams) => {
      console.log(`🎬 비디오 업로드 시작 - videoType: ${videoType}, size: ${(videoBlob.size / 1024 / 1024).toFixed(2)}MB`);

      // 1. Presigned URL 발급
      const presignedData = await videoApi.getPresignedUrl(
        examId,
        videoType,
        videoBlob.type,
        videoBlob.size
      );

      // 2. MinIO 업로드 (재시도 로직 적용)
      await retryWithDelay(async () => {
        return videoApi.uploadToMinio(
          presignedData.uploadUrl,
          videoBlob,
          presignedData.requiredHeaders,
          onProgress  // ✅ 진행률 콜백 전달
        );
      });

      console.log('✅ MinIO 업로드 완료!');

      // 3. 서버 상태 완료 처리 (API 변경 반영)
      return await videoApi.updateVideoStatus(examId, presignedData.videoId, presignedData.s3Key, videoType);
    }
  });
};