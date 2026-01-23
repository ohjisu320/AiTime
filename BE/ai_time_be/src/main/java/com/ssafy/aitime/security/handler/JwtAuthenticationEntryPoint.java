package com.ssafy.aitime.security.handler;

import com.ssafy.aitime.common.response.ApiResponse;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.HttpStatus;
import org.springframework.security.core.AuthenticationException;
import org.springframework.security.web.AuthenticationEntryPoint;
import org.springframework.stereotype.Component;
import tools.jackson.databind.ObjectMapper;

import java.io.IOException;

/**
 * AuthenticationEntryPoint(401 ERROR)
 *  토큰없음, 토큰 만료, 토큰 변조, 토큰 서명 불일치, accessToken 없이 접근 시
 *  ==> 즉. 인증 자체 실패
 */
@Slf4j
@Component
public class JwtAuthenticationEntryPoint implements AuthenticationEntryPoint {

    private final ObjectMapper objectMapper = new ObjectMapper();

    @Override
    public void commence(HttpServletRequest request, HttpServletResponse response, AuthenticationException authException) throws IOException, ServletException {

        log.warn("[401 UNAUTHORIZED] 인증 실패: {}", authException.getMessage());

        ApiResponse<?> body = ApiResponse.of(
                HttpStatus.UNAUTHORIZED,
                "인증이 필요합니다. 토큰이 없거나 유효하지 않습니다.",
                null
        );

        response.setStatus(HttpStatus.UNAUTHORIZED.value());
        response.setContentType("application/json;charset=UTF-8");

        response.getWriter().write(objectMapper.writeValueAsString(body));
    }
}
