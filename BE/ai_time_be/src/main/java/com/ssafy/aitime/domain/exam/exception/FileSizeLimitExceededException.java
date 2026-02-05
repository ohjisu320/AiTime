package com.ssafy.aitime.domain.exam.exception;

public class FileSizeLimitExceededException extends RuntimeException {

    private static final String DEFAULT_MESSAGE = "파일 크기 제한을 초과했습니다";

    public FileSizeLimitExceededException() {
        super(DEFAULT_MESSAGE);
    }

    public FileSizeLimitExceededException(long maxSize) {
        super(DEFAULT_MESSAGE + " (최대: " + (maxSize / 1024 / 1024) + "MB)");
    }
}