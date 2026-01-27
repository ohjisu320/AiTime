package com.ssafy.aitime.domain.child.dto.request;

import com.ssafy.aitime.domain.child.entity.enums.Gender;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;

import java.time.LocalDate;

public record ChildCreateRequest(
        @NotBlank(message = "아이 이름은 필수입니다.")
        String name,
        @NotNull(message = "생년월일은 필수입니다.")
        LocalDate birthdate,
        @NotNull(message = "성별은 필수입니다.")
        Gender gender
) {
}
