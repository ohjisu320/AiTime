package com.ssafy.aitime.domain.exam.exception;

public class InvalidVideoTypeException extends RuntimeException {

    private static final String DEFAULT_MESSAGE = "유효하지 않은 비디오 타입입니다";

    public InvalidVideoTypeException() {
        super(DEFAULT_MESSAGE);
    }

    public InvalidVideoTypeException(String videoType) {
        super(DEFAULT_MESSAGE + ": " + videoType);
    }
}