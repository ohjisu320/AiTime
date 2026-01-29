import type { ApiResponse, ExamProgressData } from '../types/mission';

/**
 * API 에러 처리 헬퍼 함수
 */
async function handleApiResponse<T>(response: Response): Promise<ApiResponse<T>> {
  if (!response.ok) {
    throw new Error(`API 요청 실패: ${response.status} ${response.statusText}`);
  }

  const result: ApiResponse<T> = await response.json();

  if (result.code !== 200 || result.status !== 'OK') {
    throw new Error(result.message || 'API 응답 오류가 발생했습니다.');
  }

  return result;
}

/**
 * 검사 진행도 조회
 * GET /api/v1/exam/{examId}
 */
export async function fetchExamProgress(examId: string): Promise<ApiResponse<ExamProgressData>> {
  const response = await fetch(`/api/v1/exam/${examId}`);
  return handleApiResponse<ExamProgressData>(response);
}

/**
 * 영상 업로드 Presigned URL 발급
 * POST /api/v1/video
 */
export async function requestUploadUrl(examId: string, videoType: string): Promise<ApiResponse<{
  videoId: string;
  presignedUrl: string;
}>> {
  const response = await fetch('/api/v1/video', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ examId, videoType }),
  });
  return handleApiResponse(response);
}

/**
 * 영상 업로드 완료 확인
 * PATCH /api/v1/video/{videoId}
 */
export async function confirmUpload(videoId: string): Promise<ApiResponse<{
  videoId: string;
  status: string;
  updatedAt: string;
}>> {
  const response = await fetch(`/api/v1/video/${videoId}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ status: 'UPLOADED' }),
  });
  return handleApiResponse(response);
}

/**
 * 태스크 삭제 (재촬영)
 * DELETE /api/v1/video/{videoId}
 */
export async function deleteVideo(videoId: string): Promise<void> {
  const response = await fetch(`/api/v1/video/${videoId}`, {
    method: 'DELETE',
  });

  if (!response.ok) {
    throw new Error(`영상 삭제 실패: ${response.status}`);
  }
}