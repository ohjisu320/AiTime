package com.ssafy.aitime.domain.exam.service;

import com.ssafy.aitime.domain.exam.dto.request.PresignedKeyRequest;
import com.ssafy.aitime.domain.exam.dto.request.VideoUploadCompleteRequest;
import com.ssafy.aitime.domain.exam.dto.response.PresignedKeyResponse;
import com.ssafy.aitime.domain.exam.dto.response.VideoUploadCompleteResponse;

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
}