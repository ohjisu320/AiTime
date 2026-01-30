package com.ssafy.aitime.domain.exam.exception;

import com.ssafy.aitime.domain.child.entity.enums.ChildHomeStatus;

public class ExamNotEligibleException extends RuntimeException {
    public ExamNotEligibleException() {
        super("현재 검사를 시작할 수 없는 상태입니다. 현재 상태: %s");
    }
}