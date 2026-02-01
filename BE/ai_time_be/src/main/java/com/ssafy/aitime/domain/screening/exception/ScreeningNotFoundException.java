package com.ssafy.aitime.domain.screening.exception;

public class ScreeningNotFoundException extends RuntimeException{

    public ScreeningNotFoundException() {
        super("스크리닝 세션을 찾을 수 없습니다.");
    }

    public ScreeningNotFoundException(String message) {
        super(message);
    }
}
