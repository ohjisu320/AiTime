package com.ssafy.aitime.domain.exam.service;

import com.ssafy.aitime.domain.exam.dto.request.PresignedUrlRequest;
import com.ssafy.aitime.domain.exam.dto.response.PresignedUrlResponse;

import java.util.UUID;

public interface VideoService {
    /**
     * 특정 검사에 대한 S3 영상 업로드 Presigned URL 발급
     */
    PresignedUrlResponse generatePresignedUploadUrl(UUID examId, PresignedUrlRequest request);
}