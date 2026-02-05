package com.ssafy.aitime.common.exception.commonExceptions;

public class InsertFailedException extends RuntimeException {
	private static final long serialVersionUID = 1L;
	public InsertFailedException() {
        super("저장에 실패했습니다.");
    }

    public InsertFailedException(String message) {
        super(message);
    }
}
