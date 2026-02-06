package com.ssafy.aitime.domain.child.entity.enums;

/**
 * 아이 홈 화면에서의 검사 상태를 나타내는 Enum
 * 기존의 여러 boolean 값들을 하나의 명확한 상태로 통합
 */
public enum ChildHomeStatus {
    /**
     * 초대코드 미등록 상태
     * - 병원 코드가 등록되지 않음
     */
    NEED_HOSPITAL,

    /**
     * 검사 가능 - 처음 시작
     * - 초대코드 등록 완료
     * - 검사 시작 전 OR 이전 검사 완료 후 3개월 경과
     */
    AVAILABLE,

    /**
     * 검사 가능 - 데이터 삭제됨
     * - 검사를 시작했으나 3일이 경과하여 임시 데이터가 삭제됨
     * - 새로 시작해야 함
     */
    AVAILABLE_EXPIRED,

    /**
     * 검사 진행 중
     * - 검사 시작 후 3일 이내
     * - 1~3개의 비디오가 업로드됨
     */
    IN_PROGRESS,

    /**
     * 검사 완료, 대기 기간
     * - 검사 완료 (4개 비디오 모두 업로드)
     * - 다음 검사 가능일까지 3개월 미만
     */
    COOLDOWN,

    /**
     * 대기 기간 - 초대코드 재등록 예약일 전
     * - 2번째 병원 초대코드 등록 시
     * - 예약일이 nextEligibleAt 이전인 경우
     * - 기존 검사를 이어서 진행해야 하는 상태
     */
    COOLDOWN_BEFORE
}
