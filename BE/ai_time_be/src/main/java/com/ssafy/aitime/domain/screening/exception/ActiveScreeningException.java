package com.ssafy.aitime.domain.screening.exception;

public class ActiveScreeningException extends RuntimeException{
    public ActiveScreeningException() {
        super("이미 진행 중인 스크리닝이 있습니다.");
    }
}
