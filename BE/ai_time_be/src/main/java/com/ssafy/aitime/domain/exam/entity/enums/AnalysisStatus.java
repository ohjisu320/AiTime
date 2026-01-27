package com.ssafy.aitime.domain.exam.entity.enums;

/*
    null,       // 분석 전 (AI 검사 버튼 안 누름)
    PENDING,    // AI 검사 버튼 클릭 (분석 대기)
    PROCESSING, // 분석 중
    SUCCESS,    // 분석 완료
    FAILED      // 분석 실패 (재검사 가능)
 */
public enum AnalysisStatus {
    PENDING, PROCESSING, SUCCESS, FAILED
}
