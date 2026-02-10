package com.ssafy.aitime.common.exception.commonExceptions;

public class UpdateFailedException extends RuntimeException {
	private static final long serialVersionUID = 1L;
	public UpdateFailedException() {
        super("업데이트에 실패했습니다.");
    }

    public UpdateFailedException(String message) {
        super(message);
    }
}
