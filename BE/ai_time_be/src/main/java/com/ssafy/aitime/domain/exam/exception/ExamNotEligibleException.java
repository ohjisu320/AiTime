package com.ssafy.aitime.domain.exam.exception;

public class ExamNotEligibleException extends RuntimeException {
    public ExamNotEligibleException() {
        super("현재 검사를 시작할 수 없는 상태입니다.");
    }
}