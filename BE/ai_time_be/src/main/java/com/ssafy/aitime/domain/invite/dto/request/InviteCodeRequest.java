package com.ssafy.aitime.domain.invite.dto.request;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;

import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.UUID;

public record InviteCodeRequest(
        @NotBlank(message = "아이 이름은 필수입니다.") String childName,
        @NotNull(message = "아이 생년월일은 필수입니다.") LocalDate childBirthdate,
        @NotBlank(message = "보호자 전화번호는 필수입니다.") String parentPhone,
        @NotNull(message = "예약 일시는 필수입니다.") LocalDateTime scheduledAt,
        UUID doctorId
) {
}
