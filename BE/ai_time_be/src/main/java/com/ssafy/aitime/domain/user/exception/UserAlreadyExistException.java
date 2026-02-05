package com.ssafy.aitime.domain.user.exception;

public class UserAlreadyExistException extends RuntimeException {
	private static final long serialVersionUID = 1L;

	public UserAlreadyExistException() {
        super("이미 존재하는 유저입니다.");
    }
}
