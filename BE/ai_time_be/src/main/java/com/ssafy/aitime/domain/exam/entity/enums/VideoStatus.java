package com.ssafy.aitime.domain.exam.entity.enums;

/*
    PENDING_UPLOAD,     // S3업로드 전 PresignedUrl 발급 후
    UPLOADED,        // S3 업로드 완료, AI 검사 전
 */
public enum VideoStatus {
    PENDING_UPLOAD,
    UPLOADED
}
