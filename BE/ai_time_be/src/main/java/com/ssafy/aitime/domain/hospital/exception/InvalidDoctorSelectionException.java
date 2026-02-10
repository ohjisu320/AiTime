package com.ssafy.aitime.domain.hospital.exception;

public class InvalidDoctorSelectionException extends RuntimeException {

    public InvalidDoctorSelectionException() {
        super("해당 병원에 소속된 유효한 의사가 아닙니다.");
    }
}


