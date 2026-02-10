package com.ssafy.aitime.domain.exam.dto.response;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Builder;

@Builder
public record PoseImitationTimestampInfo(
        @JsonProperty("parentStartTime")
        Double parentStartTime,

        @JsonProperty("parentEndTime")
        Double parentEndTime,

        @JsonProperty("childStartTime")
        Double childStartTime,

        @JsonProperty("childEndTime")
        Double childEndTime,

        @JsonProperty("trialIndex")
        Integer trialIndex
) {
}
