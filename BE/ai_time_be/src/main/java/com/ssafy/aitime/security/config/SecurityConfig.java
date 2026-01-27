package com.ssafy.aitime.security.config;

import com.ssafy.aitime.security.filter.JwtAuthenticationFilter;
import com.ssafy.aitime.security.provider.JwtTokenProvider;
import lombok.RequiredArgsConstructor;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.security.authentication.AuthenticationManager;
import org.springframework.security.config.annotation.authentication.configuration.AuthenticationConfiguration;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configurers.AbstractHttpConfigurer;
import org.springframework.security.config.http.SessionCreationPolicy;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.security.web.AuthenticationEntryPoint;
import org.springframework.security.web.SecurityFilterChain;
import org.springframework.security.web.access.AccessDeniedHandler;
import org.springframework.security.web.authentication.UsernamePasswordAuthenticationFilter;
import org.springframework.web.cors.CorsConfiguration;
import org.springframework.web.cors.CorsConfigurationSource;
import org.springframework.web.cors.UrlBasedCorsConfigurationSource;

import java.util.Arrays;
import java.util.Collections;

@Configuration
@RequiredArgsConstructor
public class SecurityConfig {

    private final StringRedisTemplate redisTemplate;
    // 비밀번호 암호화
    @Bean
    public PasswordEncoder passwordEncoder() {
        return new BCryptPasswordEncoder();
    }

    // 스프링 시큐리티 내 로그인 관련 객체
    @Bean
    public AuthenticationManager authenticationManager(AuthenticationConfiguration configuration) throws Exception {
        return configuration.getAuthenticationManager();
    }

    @Bean
    public SecurityFilterChain securityFilterChain(HttpSecurity http, JwtTokenProvider jwtTokenProvider, AuthenticationEntryPoint authenticationEntryPoint, AccessDeniedHandler accessDeniedHandler) throws Exception {
        http
                .cors(cors -> cors.configurationSource(corsConfigurationSource()))
                .csrf(AbstractHttpConfigurer::disable)
                .httpBasic(AbstractHttpConfigurer::disable)
                .formLogin(AbstractHttpConfigurer::disable)
                .sessionManagement(session -> session.sessionCreationPolicy(SessionCreationPolicy.STATELESS))
                .exceptionHandling(exception -> exception
                        .authenticationEntryPoint(authenticationEntryPoint) // 401 ERROR
                        .accessDeniedHandler(accessDeniedHandler)           // 403 ERROR
                )
                .authorizeHttpRequests(auth -> auth
                        .requestMatchers(
                                "/user/join",
                                "/user/login",
                                "/user/refresh",
                                "/user/logout",
                                "/user/duplicate-id",
                                "/user/get-id",
                                "/user/verify-identity",
                                "/user/password",
                                "/auth/**",
                                "/v3/api-docs/**",
                                "/swagger-ui/**",
                                "/swagger-ui.html",
                                "/test/rabbitmq/**"
                        ).permitAll()
                        .requestMatchers("/error").permitAll()
                        .anyRequest().authenticated()
                )
                .addFilterBefore(new JwtAuthenticationFilter(jwtTokenProvider, redisTemplate), UsernamePasswordAuthenticationFilter.class);

        return http.build();
    }

    @Bean
    public CorsConfigurationSource corsConfigurationSource() {
        CorsConfiguration configuration = new CorsConfiguration();

        // 프론트엔드 주소 허용
        configuration.setAllowedOrigins(Collections.singletonList("http://localhost:5173"));

        // 허용할 HTTP 메서드
        configuration.setAllowedMethods(Arrays.asList("GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"));

        // 허용할 헤더
        configuration.setAllowedHeaders(Collections.singletonList("*"));

        // 쿠키 및 인증 정보 허용 (필수)
        configuration.setAllowCredentials(true);

        // 프론트엔드에서 읽을 수 있는 헤더 노출 (토큰 관련)
        configuration.setExposedHeaders(Arrays.asList("Authorization", "Set-Cookie"));

        UrlBasedCorsConfigurationSource source = new UrlBasedCorsConfigurationSource();
        // 모든 경로에 대해 위 설정 적용
        source.registerCorsConfiguration("/**", configuration);
        return source;
    }
}
