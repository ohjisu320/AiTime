import axios from 'axios';

export const videoApi = {
  /** 1단계: Presigned URL 발급 요청 */
  getPresignedUrl: async (examId: string, videoType: string) => {
    const { data } = await axios.post('/video', { examId, videoType });
    return data.data; // { videoId, presignedUrl }
  },

  /** 2단계: S3 직접 업로드 (Authorization 헤더 제거 필수) */
  uploadToS3: async (url: string, file: Blob) => {
    return axios.put(url, file, {
      headers: { 'Content-Type': 'video/mp4' },
      transformRequest: [(data, headers) => {
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
    const { data } = await axios.patch(`/video/${videoId}`, {
      status: "UPLOADED",
      attempts // 태스크 내 시도 구간 정보
    });
    return data.data;
  }
};