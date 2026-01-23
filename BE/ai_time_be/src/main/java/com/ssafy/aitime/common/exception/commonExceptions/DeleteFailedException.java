package com.ssafy.aitime.common.exception.commonExceptions;

public class DeleteFailedException extends RuntimeException {
	private static final long serialVersionUID = 1L;
	public DeleteFailedException() {
        super("삭제에 실패했습니다.");
    }

    public DeleteFailedException(String message) {
        super(message);
    }
}
