package com.ssafy.aitime.domain.exam.exception;

public class PresignedUrlGenerationException extends RuntimeException {

    public PresignedUrlGenerationException(String s3Key) {
        super("Presigned URL 생성 실패: " + s3Key);
    }

    public PresignedUrlGenerationException(String s3Bucket, String s3Key) {
        super(String.format("Presigned URL 생성 실패 - bucket: %s, key: %s", s3Bucket, s3Key));
    }

    public PresignedUrlGenerationException(String s3Key, Throwable cause) {
        super("Presigned URL 생성 실패: " + s3Key, cause);
    }
}