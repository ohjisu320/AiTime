package com.ssafy.aitime.domain.exam.dto.response;

import com.fasterxml.jackson.annotation.JsonProperty;
import com.ssafy.aitime.domain.exam.service.dto.VideoSummary;
import lombok.Builder;

import java.time.LocalDate;
import java.util.List;

@Builder
public record ExamWithVideosResponse(
        @JsonProperty("examId")
        String examId,

        @JsonProperty("examDate")
        LocalDate examDate,

        @JsonProperty("examStatus")
        String examStatus,

        @JsonProperty("videos")
        List<VideoSummary> videos
) {
}
