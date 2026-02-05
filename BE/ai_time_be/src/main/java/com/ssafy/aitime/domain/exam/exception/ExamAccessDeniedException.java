package com.ssafy.aitime.domain.exam.exception;

import java.util.UUID;

/**
 * 검사에 대한 접근 권한이 없을 때 발생하는 예외
 */
public class ExamAccessDeniedException extends RuntimeException {
    public ExamAccessDeniedException(UUID examId) {
        super(String.format("검사에 대한 접근 권한이 없습니다: %s", examId));
    }
}