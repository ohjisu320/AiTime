package com.ssafy.aitime.domain.exam.exception;

public class ExamStatusNotAllowedException extends RuntimeException {

    private static final String DEFAULT_MESSAGE = "이미 완료된 검사입니다";

    public ExamStatusNotAllowedException() {
        super(DEFAULT_MESSAGE);
    }

    public ExamStatusNotAllowedException(String reason) {
        super(DEFAULT_MESSAGE + ": " + reason);
    }
}