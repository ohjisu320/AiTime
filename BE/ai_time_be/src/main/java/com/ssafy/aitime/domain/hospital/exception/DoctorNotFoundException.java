package com.ssafy.aitime.domain.hospital.exception;

/**
 * 의사를 찾을 수 없을 때 발생하는 예외
 */
public class DoctorNotFoundException extends RuntimeException {
    
    public DoctorNotFoundException() {
        super("존재하지 않거나 활성화되지 않은 의사입니다.");
    }
}
