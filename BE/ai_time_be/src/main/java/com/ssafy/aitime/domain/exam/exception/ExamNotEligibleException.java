package com.ssafy.aitime.domain.exam.exception;

public class ExamNotEligibleException extends RuntimeException {
    public ExamNotEligibleException(String message) {
        super(message);
    }
}