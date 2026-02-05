package com.ssafy.aitime.domain.exam.dto.response;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Builder;

@Builder
public record TimestampInfo(
        @JsonProperty("startS")
        Double startS,

        @JsonProperty("endS")
        Double endS,

        @JsonProperty("trialIndex")
        Integer trialIndex
) {
}
