package com.ssafy.aitime.infra.rabbitmq.dto.message;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.List;
import java.util.UUID;

/**
 * AI 분석 결과 메시지 DTO
 * API 명세서에 맞게 수정됨
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class AnalysisResultMessage {

    @JsonProperty("examId")
    private UUID examId;

    @JsonProperty("videoId")
    private UUID videoId;

    @JsonProperty("videoType")
    private String videoType;

    @JsonProperty("analyzedAt")
    private String analyzedAt;

    @JsonProperty("status")
    private String status;

    @JsonProperty("metrics")
    private MetricsData metrics;

    @JsonProperty("ADOS")
    private AdosData ados;

    // Task 번호를 videoType에서 추출
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
     * Metrics 데이터
     */
    @Data
    @NoArgsConstructor
    @AllArgsConstructor
    public static class MetricsData {
        @JsonProperty("per_trial")
        private List<TrialMetric> perTrial;
    }

    /**
     * Trial별 메트릭 데이터
     * 모든 Task의 필드를 포함 (각 Task는 필요한 필드만 사용)
     */
    @Data
    @NoArgsConstructor
    @AllArgsConstructor
    public static class TrialMetric {
        // 공통 필드
        @JsonProperty("trial_index")
        private Integer trialIndex;

        @JsonProperty("success")
        private Boolean success;

        @JsonProperty("latency_s")
        private Double latencyS;

        // ========== Task 1: PoseImitation 필드 ==========
        @JsonProperty("action_type")
        private String actionType;

        @JsonProperty("similarity_score")
        private Double similarityScore;

        @JsonProperty("parent_start_time")
        private Double parentStartTime;

        @JsonProperty("parent_end_time")
        private Double parentEndTime;

        @JsonProperty("child_start_time")
        private Double childStartTime;

        @JsonProperty("child_end_time")
        private Double childEndTime;

        @JsonProperty("duration_s")
        private Double durationS;

        @JsonProperty("attention_ratio")
        private Double attentionRatio;

        // ========== Task 2: SpeechImitation 필드 ==========
        @JsonProperty("trial_start_s")
        private Double trialStartS;

        @JsonProperty("trial_end_s")
        private Double trialEndS;

        @JsonProperty("stimulus_id")
        private String stimulusId;

        @JsonProperty("stimulus_text")
        private String stimulusText;

        @JsonProperty("response_detected")
        private Boolean responseDetected;

        @JsonProperty("failure_reason")
        private String failureReason;

        @JsonProperty("freq_abnormal")
        private Boolean freqAbnormal;

        // ========== Task 3: NameFacing 필드 ==========
        @JsonProperty("gaze_duration_s")
        private Double gazeDurationS;

        @JsonProperty("emotion")
        private String emotion;

        // ========== Task 4: NameNonFacing 필드 ==========
        @JsonProperty("trigger_start_s")
        private Double triggerStartS;

        @JsonProperty("trigger_end_s")
        private Double triggerEndS;

        @JsonProperty("trigger_text")
        private String triggerText;

        @JsonProperty("voice_detected")
        private Boolean voiceDetected;

        @JsonProperty("voice_start_s")
        private Double voiceStartS;

        @JsonProperty("voice_end_s")
        private Double voiceEndS;

        @JsonProperty("voice_duration_s")
        private Double voiceDurationS;

        @JsonProperty("voice_confidence")
        private Double voiceConfidence;

        @JsonProperty("gaze_match")
        private Boolean gazeMatch;

        @JsonProperty("head_yaw_deg")
        private Double headYawDeg;

        @JsonProperty("head_pitch_deg")
        private Double headPitchDeg;
    }

    /**
     * ADOS 데이터
     * API에서 Boolean 또는 Integer로 전송됨
     */
    @Data
    @NoArgsConstructor
    @AllArgsConstructor
    public static class AdosData {
        // Task 1: PoseImitation
        @JsonProperty("B6")
        private Object b6;      // Boolean (TRUE/FALSE)

        @JsonProperty("A8")
        private Object a8;      // Integer (0-3)

        @JsonProperty("B18")
        private Object b18;     // Boolean (TRUE/FALSE)

        // Task 2: SpeechImitation
        @JsonProperty("A3")
        private Object a3;      // Integer (0-3)

        // Task 3: NameFacing
        @JsonProperty("B1")
        private Object b1;      // Integer (0-3)

        @JsonProperty("B4")
        private Object b4;      // Integer (0-3)

        // Task 4: NameNonFacing
        @JsonProperty("B7")
        private Object b7;      // Integer (0-3)

        // 모든 필드를 Object로 선언하여 유연하게 처리
        // 실제 타입은 서비스에서 변환
    }
}
