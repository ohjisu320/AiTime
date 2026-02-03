import axios from 'axios';
import api from '@/api/axiosConfig';

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

    const { data } = await api.post(
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
    onProgressCallback?: (progress: number) => void
  ) => {
    console.log('📤 MinIO 업로드 시작...');

    try {
      return await axios.put(uploadUrl, file, {
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
          if (headers) {
            // "Cannot convert undefined or null to object" 에러 방지
            // headers가 AxiosHeaders 객체인 경우 common 프로퍼티 접근 시 안전장치 필요
            if ((headers as any).common) {
              delete (headers as any).common['Authorization'];
            }

            // headers 객체 자체에서 삭제 시도
            if ('Authorization' in headers) {
              delete headers['Authorization'];
            } else if ((headers as any).delete) {
              // AxiosHeaders 객체 메서드 사용
              (headers as any).delete('Authorization');
            }
          }
          return data;
        }],
        responseType: 'text',
        validateStatus: (status) => status >= 200 && status < 300,
        transformResponse: [(data) => data]
      });
    } catch (error: any) {
      console.error('❌ MinIO 업로드 실패:', error);

      if (error.response) {
        // 서버가 응답을 주었으나 2xx가 아닌 경우
        console.error('응답 데이터:', error.response.data);
        console.error('응답 상태:', error.response.status);
        console.error('응답 헤더:', error.response.headers);
      } else if (error.request) {
        // 요청은 갔으나 응답을 못 받은 경우 (CORS, 네트워크 등)
        console.error('응답 없음 (Network/CORS Error):', error.request);
      } else {
        // 요청 설정 중 에러 발생
        console.error('요청 설정 에러:', error.message);
      }
      throw error;
    }
  },

  /** 3단계: 백엔드 상태 업데이트 */
  /** 3단계: 백엔드 상태 업데이트 */
  updateVideoStatus: async (
    examId: string,
    videoId: string,
    s3Key: string,
    videoType: VideoType
  ) => {
    console.log(`📤 비디오 상태 업데이트: ${videoId} (Exam: ${examId}, Type: ${videoType})`);

    try {
      console.log(`📤 완료 요청 Payload:`, { videoId, s3Key, videoType });
      // 404 에러 수정 시도: videoId를 path에서 제거하고 body에 포함
      // 400 에러 수정 시도: videoType 추가
      const { data } = await api.post(`/exam/${examId}/videos/complete`, {
        videoId,
        s3Key,
        videoType
      });

      console.log('✅ 상태 업데이트 완료');
      return data.data;
    } catch (error: any) {
      console.error('❌ 비디오 상태 업데이트 실패:', error);
      if (error.response) {
        console.error('응답 상태:', error.response.status);
        console.error('응답 데이터 (JSON):', JSON.stringify(error.response.data, null, 2));
        console.error('요청 URL:', error.config?.url);
        console.error('요청 Body:', error.config?.data);

        // 이미 업로드 완료된 상태라면 에러를 무시하고 성공으로 처리
        if (error.response.data?.message?.includes("현재 비디오 상태(UPLOADED)에서는")) {
          console.log('⚠️ 이미 업로드 완료된 비디오입니다. (성공 처리)');
          return { status: 'ALREADY_UPLOADED' };
        }
      }
      throw error;
    }
  }
};