package com.ssafy.aitime.domain.hospital.exception;

public class HospitalChildrenNotFoundException extends RuntimeException {

    public HospitalChildrenNotFoundException() {
        super("존재하지 않는 병원_자녀 정보입니다.");
    }

}