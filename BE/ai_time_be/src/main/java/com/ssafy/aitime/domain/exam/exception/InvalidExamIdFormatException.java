package com.ssafy.aitime.domain.exam.exception;

public class InvalidExamIdFormatException extends RuntimeException {

    private static final String DEFAULT_MESSAGE = "유효하지 않은 examId 형식입니다";

    public InvalidExamIdFormatException() {
        super(DEFAULT_MESSAGE);
    }

    public InvalidExamIdFormatException(String examId) {
        super(DEFAULT_MESSAGE + ": " + examId);
    }
}