package com.ssafy.aitime.domain.hospital.exception;

public class HospitalAlreadyLinkedException extends RuntimeException {

    public HospitalAlreadyLinkedException() {
        super("이미 해당 병원과 연동되어 있습니다.");
    }
}