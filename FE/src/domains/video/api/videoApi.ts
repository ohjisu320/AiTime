import axios from 'axios';

// ==================== Type Definitions ====================

export type VideoType =
  | 'POSE_IMITATION'
  | 'SPEECH_IMITATION'
  | 'NAME_FACING'
  | 'NAME_NON_FACING';

interface PresignUploadRequest {
  videoType: VideoType;
  contentType: string;
  contentLength: number;
}

interface PresignUploadResponse {
  videoId: string;
  uploadUrl: string;
  s3Key: string;
  requiredHeaders: {
    'Content-Type': string;
  };
}

// ==================== API Functions ====================

export const videoApi = {
  /** 1단계: Presigned URL 발급 요청 (MinIO) */
  getPresignedUrl: async (
    examId: string,
    videoType: VideoType,
    contentType: string,
    contentLength: number
  ): Promise<PresignUploadResponse> => {
    const requestBody: PresignUploadRequest = {
      videoType,
      contentType,
      contentLength
    };

    console.log(`📤 [Presigned URL 요청] examId: ${examId}, videoType: ${videoType}`);

    const { data } = await axios.post(
      `/exam/${examId}/videos/presign-upload`,
      requestBody
    );

    console.log('✅ Presigned URL 발급 완료:', data.data);
    return data.data;
  },

  /** 2단계: MinIO 직접 업로드 (Authorization 헤더 제거 필수) */
  uploadToMinio: async (
    uploadUrl: string,
    file: Blob,
    requiredHeaders: { 'Content-Type': string },
    onProgressCallback?: (progress: number) => void  // ✅ 진행률 콜백 추가
  ) => {
    console.log('📤 MinIO 업로드 시작...');

    return axios.put(uploadUrl, file, {
      headers: {
        'Content-Type': requiredHeaders['Content-Type']
      },
      onUploadProgress: (progressEvent) => {
        if (onProgressCallback && progressEvent.total) {
          const percentCompleted = Math.round(
            (progressEvent.loaded * 100) / progressEvent.total
          );
          onProgressCallback(percentCompleted);
        }
      },
      transformRequest: [(data, headers) => {
        // MinIO Presigned URL은 Authorization 헤더가 있으면 안됨
        if (headers) {
          delete headers.common['Authorization'];
          delete headers['Authorization'];
        }
        return data;
      }]
    });
  },

  /** 3단계: 백엔드 상태 업데이트 (Attempt 데이터 포함) */
  updateVideoStatus: async (videoId: string, attempts: any[]) => {
    console.log(`📤 비디오 상태 업데이트: ${videoId}`);

    const { data } = await axios.patch(`/video/${videoId}`, {
      status: "UPLOADED",
      attempts // 태스크 내 시도 구간 정보
    });

    console.log('✅ 상태 업데이트 완료');
    return data.data;
  }
};