package com.ssafy.aitime.domain.exam.exception;

/**
 * S3에 파일이 실제로 존재하지 않거나 접근할 수 없을 때 발생하는 예외
 */
public class S3FileVerificationException extends RuntimeException {
    public S3FileVerificationException(String s3Url) {
        super(String.format("S3 파일 검증에 실패했습니다. 파일이 존재하지 않거나 접근할 수 없습니다: %s", s3Url));
    }

    public S3FileVerificationException(String s3Url, Throwable cause) {
        super(String.format("S3 파일 검증 중 오류가 발생했습니다: %s", s3Url), cause);
    }
}