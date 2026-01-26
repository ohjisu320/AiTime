package com.ssafy.aitime.domain.hospital.exception;

/**
 * 의사를 찾을 수 없을 때 발생하는 예외
 */
public class DoctorNotFoundException extends RuntimeException {
    
    public DoctorNotFoundException(String message) {
        super(message);
    }
    
    public DoctorNotFoundException(String message, Throwable cause) {
        super(message, cause);
    }
}
