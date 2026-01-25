package com.ssafy.aitime.domain.auth.service;

import com.ssafy.aitime.domain.auth.dto.response.PhoneVerificationResponse;
import com.ssafy.aitime.infra.sms.SmsUtil;
import lombok.RequiredArgsConstructor;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.stereotype.Service;

import java.time.Duration;
import java.time.LocalDateTime;

@Service
@RequiredArgsConstructor
public class AuthServiceImpl implements AuthService {

    private final SmsUtil smsUtil;
    private final StringRedisTemplate redisTemplate;

    private static final long VERIFICATION_EXPIRE_TIME = 300L; // 5분

    @Override
    public PhoneVerificationResponse sendVerificationCode(String phoneNumber) {
// 1. 6자리 랜덤 인증번호 생성
        String code = String.valueOf((int)(Math.random() * 899999) + 100000);
        LocalDateTime expiredAt = LocalDateTime.now().plusMinutes(5); // 5분 뒤 만료

        // 2. Redis에 저장 (Key: 휴대폰번호, Value: 인증번호)
        redisTemplate.opsForValue().set(
                "SMS_CODE:" + phoneNumber,
                code,
                Duration.ofSeconds(VERIFICATION_EXPIRE_TIME)
        );

        // 3. 문자 발송
        smsUtil.sendVerificationCode(phoneNumber, code);

        return PhoneVerificationResponse.of(phoneNumber, expiredAt);
    }
}
