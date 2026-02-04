package com.ssafy.aitime.security.config;

import com.ssafy.aitime.security.filter.JwtAuthenticationFilter;
import com.ssafy.aitime.security.provider.JwtTokenProvider;
import com.ssafy.aitime.security.service.CustomHospitalStaffDetailsService;
import com.ssafy.aitime.security.service.CustomUserDetailsService;
import lombok.RequiredArgsConstructor;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Primary;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.security.authentication.AuthenticationManager;
import org.springframework.security.authentication.ProviderManager;
import org.springframework.security.authentication.dao.DaoAuthenticationProvider;
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

    // 두 개의 전용 서비스 주입
    private final CustomUserDetailsService userDetailsService;
    private final CustomHospitalStaffDetailsService staffDetailsService;
    // 비밀번호 암호화
    @Bean
    public PasswordEncoder passwordEncoder() {
        return new BCryptPasswordEncoder();
    }


    // User 전용 AuthenticationManager -> 만약 주입될 빈이 없는 경우 이걸 기본으로 사용하도록 명시
    @Primary
    @Bean(name = "userAuthenticationManager")
    public AuthenticationManager userAuthenticationManager() {
        // Spring Security 6.x: 생성자에 UserDetailsService 전달
        DaoAuthenticationProvider provider = new DaoAuthenticationProvider(userDetailsService);
        provider.setPasswordEncoder(passwordEncoder());
        return new ProviderManager(provider);
    }

    // HospitalStaff 전용 AuthenticationManager
    @Bean(name = "staffAuthenticationManager")
    public AuthenticationManager staffAuthenticationManager() {
        // Spring Security 6.x: 생성자에 UserDetailsService 전달
        DaoAuthenticationProvider provider = new DaoAuthenticationProvider(staffDetailsService);
        provider.setPasswordEncoder(passwordEncoder());
        return new ProviderManager(provider);
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
                                "/hospital-staff/login",
                                "/hospital-staff/refresh",
                                "/auth/**",
                                "/v3/api-docs/**",
                                "/swagger-ui/**",
                                "/swagger-ui.html",
                                "/hospital-staff/dummy", // 더미데이터 생성용
                                "/screening/**",          // 스크리닝
                                "/livekit/**" ,           // 스크리닝
                                "/test/**"
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
        configuration.setAllowedOrigins(Arrays.asList(
                "http://localhost:5173",
                "http://localhost:3000",  // 테스트용
                "http://127.0.0.1:3000",  // 127.0.0.1도 추가
                "http://localhost:5500",  // VS Code Live Server
                "null"                     // 파일 직접 열기 (file://)
        ));

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
