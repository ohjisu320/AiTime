package com.ssafy.aitime.security.filter;

import com.ssafy.aitime.security.provider.JwtTokenProvider;
import io.jsonwebtoken.JwtException;
import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.web.filter.OncePerRequestFilter;

import java.io.IOException;

@Slf4j
@RequiredArgsConstructor
public class JwtAuthenticationFilter extends OncePerRequestFilter {

    private final JwtTokenProvider jwtTokenProvider;

    @Override
    protected void doFilterInternal(HttpServletRequest request, HttpServletResponse response, FilterChain filterChain) throws ServletException, IOException {
        try{
            String authHeader = request.getHeader("Authorization");

//            System.out.println(authHeader);
            // Authorization: Bearer <token>
            if(authHeader != null && authHeader.startsWith("Bearer ")) {
                String token = authHeader.substring(7);

                if(jwtTokenProvider.validateToken(token)) {
                    Authentication authentication = jwtTokenProvider.getAuthentication(token);
                    SecurityContextHolder.getContext().setAuthentication(authentication);
                }
            }

            filterChain.doFilter(request, response);
        }catch(JwtException | IllegalArgumentException e){
            log.error("JWT 인증 실패: {}", e.getMessage());
            setErrorResponse(response, "유효하지 않은 토큰입니다: " + e.getMessage());
        }
    }

    private void setErrorResponse(HttpServletResponse response, String message) throws IOException {
        response.setStatus(HttpServletResponse.SC_UNAUTHORIZED); // 401 상태코드
        response.setContentType("application/json;charset=UTF-8");
        response.getWriter().write(
                "{" +
                        "\"status\": 401," +
                        "\"error\": \"Unauthorized\"," +
                        "\"message\": \"" + message + "\"" +
                        "}"
        );
    }
}
