package com.ssafy.aitime.domain.child.dto.request;

import jakarta.validation.constraints.NotBlank;

public record ChildHospitalLinkRequest(
        @NotBlank(message = "초대 코드는 필수입니다.")
        String inviteCode
) {
}
