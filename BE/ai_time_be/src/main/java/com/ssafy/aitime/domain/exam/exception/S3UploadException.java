package com.ssafy.aitime.domain.exam.exception;

public class S3UploadException extends RuntimeException {

    private static final String DEFAULT_MESSAGE = "S3 업로드 URL 생성에 실패했습니다";

    public S3UploadException() {
        super(DEFAULT_MESSAGE);
    }

    public S3UploadException(Throwable cause) {
        super(DEFAULT_MESSAGE, cause);
    }
}