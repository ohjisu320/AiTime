package com.ssafy.aitime.domain.exam.service.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Builder;

@Builder
public record VideoSummary(
        @JsonProperty("videoId")
        String videoId,

        @JsonProperty("videoType")
        String videoType
) {
}
