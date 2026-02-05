package com.ssafy.aitime.domain.exam.service;

import com.ssafy.aitime.domain.exam.dto.request.PresignedKeyRequest;
import com.ssafy.aitime.domain.exam.dto.request.VideoUploadCompleteRequest;
import com.ssafy.aitime.domain.exam.dto.response.*;

import java.util.UUID;

public interface VideoService {
    /**
     * 특정 검사에 대한 S3 영상 업로드 Presigned URL 발급
     */
    PresignedKeyResponse generatePresignedUploadKey(UUID userId, UUID examId, PresignedKeyRequest request);

    /**
     * 영상 업로드 완료 처리
     */
    VideoUploadCompleteResponse completeVideoUpload(UUID userId, UUID examId, UUID videoId, VideoUploadCompleteRequest request);

    /**
     * 영상 조회용 Presigned URL 생성
     * - User 또는 HospitalStaff 모두 호출 가능
     * - Principal 타입에 따라 권한 검증 로직 분기
     */
    PresignedViewUrlResponse generatePresignedViewUrl(Object principal, UUID examId, UUID videoId, int expiresInSec);

    /**
     * 비디오 재생용 Presigned URL 생성 + 이벤트 타임스탬프 조회 (의료진 전용 API)
     */
    PresignedViewUrlWithTimestampsResponse generatePresignedViewUrlWithTimestamps(Object principal, UUID examId, UUID videoId, int expiresInSec);

    /**
     * 특정 영상 삭제 (자녀/보호자 권한 검증 + MinIO 파일 삭제)
     * DB는 soft delete로 처리 (status를 DELETED로 변경)
     */
    VideoDeleteResponse deleteVideo(UUID userId, UUID examId, UUID videoId);
}