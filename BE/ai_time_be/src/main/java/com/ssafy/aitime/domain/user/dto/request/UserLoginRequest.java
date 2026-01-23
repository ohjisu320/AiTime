package com.ssafy.aitime.domain.user.dto.request;

import jakarta.validation.constraints.NotBlank;

public record UserLoginRequest (
    @NotBlank String loginId,
    @NotBlank String password
){}
