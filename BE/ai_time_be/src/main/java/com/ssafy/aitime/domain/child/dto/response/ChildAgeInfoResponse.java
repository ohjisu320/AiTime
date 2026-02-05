package com.ssafy.aitime.domain.child.dto.response;

import lombok.Builder;
import lombok.Getter;

import java.util.UUID;

@Builder
public record ChildAgeInfoResponse(
        UUID childId,
        long ageInMonths,      // 개월 수
        boolean underEighteen  // 18개월 미만 여부
) { }
