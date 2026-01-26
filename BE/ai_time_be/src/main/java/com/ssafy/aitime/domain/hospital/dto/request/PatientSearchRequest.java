package com.ssafy.aitime.domain.hospital.dto.request;

import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import org.springframework.format.annotation.DateTimeFormat;

import java.time.LocalDate;

/**
 * 환자 목록 조회 검색 조건 DTO
 */
public record PatientSearchRequest(

        @DateTimeFormat(iso = DateTimeFormat.ISO.DATE)
        LocalDate date,

        Integer year,

        Integer month,

        Integer day,

        String name,

        String resultStatus,

        @Min(0)
        Integer page,

        @Min(1)
        @Max(100)
        Integer size
) {
    /**
     * 기본값을 적용한 생성자
     */
    public PatientSearchRequest {
        page = (page != null) ? page : 0;
        size = (size != null) ? size : 10;
    }

    /**
     * 날짜 관련 파라미터가 있는지 확인
     */
    public boolean hasDateFilter() {
        return date != null || year != null || month != null || day != null;
    }

    /**
     * date 우선, 없으면 year/month/day로 LocalDate 생성
     */
    public LocalDate getEffectiveDate() {
        if (date != null) {
            return date;
        }

        if (year != null && month != null && day != null) {
            return LocalDate.of(year, month, day);
        }

        return null;
    }

    /**
     * 이름 검색 조건이 있는지 확인
     */
    public boolean hasNameFilter() {
        return name != null && !name.isBlank();
    }

    /**
     * 결과 상태 필터 조건이 있는지 확인
     */
    public boolean hasResultStatusFilter() {
        return resultStatus != null && !resultStatus.isBlank();
    }
}