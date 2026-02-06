package com.ssafy.aitime.domain.exam.dto.response;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Builder;

@Builder
public record NameFacingTimestampInfo(
        @JsonProperty("trialStartS")
        Double trialStartS,

        @JsonProperty("trialEndS")
        Double trialEndS,

        @JsonProperty("trialIndex")
        Integer trialIndex
) {
}
