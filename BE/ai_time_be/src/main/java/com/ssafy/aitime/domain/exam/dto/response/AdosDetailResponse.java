package com.ssafy.aitime.domain.exam.dto.response;

import com.fasterxml.jackson.annotation.JsonInclude;

import java.util.UUID;

public record AdosDetailResponse(
        UUID adosId,
        UUID examId,
        AdosScoresDTO scores
) {
    @JsonInclude(JsonInclude.Include.NON_NULL)
    public record AdosScoresDTO(
            // A 섹션
            Integer a2, Integer a3, Integer a7, Integer a8,
            // B 섹션
            Integer b1, Integer b4, Integer b5, Integer b6, Integer b7,
            Integer b8, Integer b9, Integer b12, Integer b13, Integer b14,
            Integer b15, Integer b16b, Integer b18,
            // 합계
            Integer socialAffectTotal,
            // D 섹션
            Integer d1, Integer d2, Integer d5,
            // 합계
            Integer rrbTotal,
            Integer total
    ) {}
}
