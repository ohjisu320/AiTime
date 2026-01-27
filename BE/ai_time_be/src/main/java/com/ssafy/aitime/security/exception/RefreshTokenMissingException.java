package com.ssafy.aitime.security.exception;

public class RefreshTokenMissingException extends RuntimeException {
	private static final long serialVersionUID = 1L;

	public RefreshTokenMissingException() {
        super("존재하지 않는 토큰입니다.");
    }
}
