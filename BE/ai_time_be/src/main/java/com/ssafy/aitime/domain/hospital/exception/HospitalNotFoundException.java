package com.ssafy.aitime.domain.hospital.exception;

public class HospitalNotFoundException extends RuntimeException {

    public HospitalNotFoundException() {
        super("존재하지 않는 병원입니다.");
    }
}


