package com.ssafy.aitime.domain.exam.exception;

/**
 * 요청된 S3 Key가 Video 엔티티의 S3 Key와 일치하지 않을 때 발생하는 예외
 */
public class S3KeyMismatchException extends RuntimeException {
    public S3KeyMismatchException(String expectedKey, String providedKey) {
        super(String.format("S3 Key가 일치하지 않습니다. 예상: %s, 제공: %s", expectedKey, providedKey));
    }
}