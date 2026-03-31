package com.ssafy.aitime.domain.exam.dto.response;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Builder;

@Builder
public record NameNonFacingTimestampInfo(
        @JsonProperty("triggerStartS")
        Double triggerStartS,

        @JsonProperty("triggerEndS")
        Double triggerEndS,

        @JsonProperty("voiceStartS")
        Double voiceStartS,

        @JsonProperty("voiceEndS")
        Double voiceEndS,

        @JsonProperty("trialIndex")
        Integer trialIndex
) {
}
