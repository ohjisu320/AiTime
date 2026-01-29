package com.ssafy.aitime.domain.hospital.exception;

public class HospitalStaffAccessDeniedException extends RuntimeException {

    public HospitalStaffAccessDeniedException() {
        super("권한이 없는 사용자 입니다.");
    }
}


