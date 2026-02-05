package com.ssafy.aitime.domain.exam.exception;

import java.util.UUID;

public class ExamNotFoundException extends RuntimeException {

    private static final String DEFAULT_MESSAGE = "검사를 찾을 수 없습니다";

    public ExamNotFoundException() {
        super(DEFAULT_MESSAGE);
    }

    public ExamNotFoundException(UUID examId) {
        super(DEFAULT_MESSAGE + ": " + examId);
    }
}