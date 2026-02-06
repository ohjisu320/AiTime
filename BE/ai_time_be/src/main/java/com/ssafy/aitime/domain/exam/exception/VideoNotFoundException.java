package com.ssafy.aitime.domain.exam.exception;

import java.util.UUID;

public class VideoNotFoundException extends RuntimeException {

    private static final String DEFAULT_MESSAGE = "비디오를 찾을 수 없습니다";

    public VideoNotFoundException() {
        super(DEFAULT_MESSAGE);
    }

    public VideoNotFoundException(UUID videoId) {
        super(DEFAULT_MESSAGE + ": " + videoId);
    }
}