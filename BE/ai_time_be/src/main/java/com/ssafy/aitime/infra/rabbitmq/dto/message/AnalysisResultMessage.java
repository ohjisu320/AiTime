package com.ssafy.aitime.infra.rabbitmq.dto.message;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Getter;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;
import java.time.ZonedDateTime;
import java.util.List;

@Getter
@NoArgsConstructor
public class AnalysisResultMessage {

    @JsonProperty("schema_version")
    private String schemaVersion;

    @JsonProperty("job_id")
    private String jobId;

    @JsonProperty("task_no")
    private Integer taskNo;

    @JsonProperty("status")
    private String status;  // "success" or "failed"

    @JsonProperty("analyzed_at")
    private ZonedDateTime analyzedAt;

    @JsonProperty("metrics")
    private Metrics metrics;

    @JsonProperty("error")
    private ErrorInfo error;

    @Getter
    @NoArgsConstructor
    public static class Metrics {
        @JsonProperty("per_trial")
        private List<TrialMetric> perTrial;
    }

    @Getter
    @NoArgsConstructor
    public static class TrialMetric {
        // ========== 공통 필드 ==========
        @JsonProperty("trial_index")
        private Integer trialIndex;

        @JsonProperty("success")
        private Boolean success;

        @JsonProperty("latency_s")
        private Double latencyS;

        // ========== task1: 동작 모방행동 (POSE_IMITATION) ==========
        @JsonProperty("similarity_score")
        private Double similarityScore;

        @JsonProperty("duration_s")
        private Double durationS;

        @JsonProperty("attention_ratio")
        private Double attentionRatio;

        // ========== task2: 발화 모방행동 (SPEECH_IMITATION) ==========
        @JsonProperty("stimulus_id")
        private String stimulusId;

        @JsonProperty("stimulus_text")
        private String stimulusText;

        @JsonProperty("response_detected")
        private Boolean responseDetected;

        @JsonProperty("failure_reason")
        private String failureReason;

        // ========== task3: 대면 호명반응 (NAME_FACING) ==========
        @JsonProperty("trial_start_s")
        private Double trialStartS;

        @JsonProperty("trial_end_s")
        private Double trialEndS;

        @JsonProperty("gaze_duration_s")
        private Double gazeDurationS;

        // ========== task4: 비대면 호명반응 (NAME_NON_FACING) ==========
        @JsonProperty("head_yaw_deg")
        private Double headYawDeg;

        @JsonProperty("head_pitch_deg")
        private Double headPitchDeg;
    }

    @Getter
    @NoArgsConstructor
    public static class ErrorInfo {
        @JsonProperty("code")
        private String code;

        @JsonProperty("message")
        private String message;
    }

    public boolean isSuccess() {
        return "success".equalsIgnoreCase(status);
    }

    public boolean isFailed() {
        return "failed".equalsIgnoreCase(status);
    }
}
