package com.ssafy.aitime.domain.child.exception;

/**
 * 자녀의 나이가 검사 가능 범위를 벗어난 경우 발생하는 예외
 */
public class ChildAgeMismatchException extends RuntimeException {
    public ChildAgeMismatchException(String message) {
        super(message);
    }
}