package com.ssafy.aitime.domain.hospital.exception;

public class HospitalStaffNotFoundException extends RuntimeException {

    public HospitalStaffNotFoundException() {
        super("존재하지 않는 직원입니다.");
    }
}


