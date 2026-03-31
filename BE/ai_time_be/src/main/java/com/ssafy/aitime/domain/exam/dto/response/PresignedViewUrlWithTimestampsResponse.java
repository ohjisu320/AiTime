package com.ssafy.aitime.domain.exam.dto.response;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Builder;

import java.time.LocalDateTime;
import java.util.List;

@Builder
public record PresignedViewUrlWithTimestampsResponse(
        @JsonProperty("videoId")
        String videoId,

        @JsonProperty("videoType")
        String videoType,

        @JsonProperty("examId")
        String examId,

        @JsonProperty("bucket")
        String bucket,

        @JsonProperty("s3Key")
        String s3Key,

        @JsonProperty("viewUrl")
        String viewUrl,

        @JsonProperty("expiresAt")
        LocalDateTime expiresAt,

        @JsonProperty("timestamps")
        List<?> timestamps  // Object 타입으로 변경하여 다양한 타입 지원
) {
}
