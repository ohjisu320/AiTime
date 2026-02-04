package com.ssafy.aitime.infra.rabbitmq.dto.message;

import com.fasterxml.jackson.annotation.JsonIgnore;
import com.fasterxml.jackson.annotation.JsonProperty;
import com.ssafy.aitime.domain.exam.entity.Video;
import lombok.Builder;
import lombok.Getter;

import java.util.UUID;

@Getter
@Builder
public class AnalysisRequestMessage {

    @JsonProperty("examId")
    private UUID examId;

    @JsonProperty("videoId")
    private UUID videoId;

    @JsonProperty("videoType")
    private String videoType;

    @JsonProperty("childName")
    private String childName;

    @JsonProperty("ageMonths")
    private Long ageMonths;

    @JsonProperty("s3Uri")
    private String s3Uri;

    // 정적 팩토리 메서드
    public static AnalysisRequestMessage from(Video video, Long ageMonths) {
        return AnalysisRequestMessage.builder()
                .examId(video.getExam().getExamId())
                .videoId(video.getVideoId())
                .videoType(video.getVideoType().name())
                .childName(video.getExam().getChild().getName())
                .ageMonths(ageMonths)
                .s3Uri(String.format("s3://%s/%s", video.getS3Bucket(), video.getS3Key()))
                .build();
    }

    /**
     * videoType으로부터 taskNo 추출
     * Queue 이름 생성용
     */
    @JsonIgnore
    public Integer getTaskNo() {
        if (videoType == null) return null;

        return switch (videoType) {
            case "POSE_IMITATION" -> 1;
            case "SPEECH_IMITATION" -> 2;
            case "NAME_FACING" -> 3;
            case "NAME_NON_FACING" -> 4;
            default -> null;
        };
    }

    /**
     * Queue 이름 반환
     */
    @JsonIgnore
    public String getQueueName() {
        Integer taskNo = getTaskNo();
        if (taskNo == null) {
            throw new IllegalStateException("Invalid videoType: " + videoType);
        }
        return "analysis.req.task" + taskNo;
    }
}
