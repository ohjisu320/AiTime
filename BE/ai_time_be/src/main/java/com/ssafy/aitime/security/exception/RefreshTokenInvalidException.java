package com.ssafy.aitime.security.exception;

public class RefreshTokenInvalidException extends RuntimeException {
	private static final long serialVersionUID = 1L;

	public RefreshTokenInvalidException() {
        super("유효하지 않은 토큰입니다.");
    }
}
