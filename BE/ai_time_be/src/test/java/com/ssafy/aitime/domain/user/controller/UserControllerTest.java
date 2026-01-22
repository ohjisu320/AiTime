package com.ssafy.aitime.domain.user.controller;

import com.ssafy.aitime.common.enums.RecordStatus;
import com.ssafy.aitime.domain.user.dto.request.UserLoginRequest;
import com.ssafy.aitime.domain.user.entity.User;
import com.ssafy.aitime.domain.user.entity.enums.UserRole;
import com.ssafy.aitime.domain.user.repository.UserRepository;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.webmvc.test.autoconfigure.AutoConfigureMockMvc;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.transaction.annotation.Transactional;
import tools.jackson.databind.ObjectMapper;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;


@SpringBootTest
@AutoConfigureMockMvc
@Transactional
class UserControllerTest {
    @Autowired
    MockMvc mockMvc;
    @Autowired
    ObjectMapper objectMapper;

    @Autowired
    UserRepository userRepository;
    @Autowired
    PasswordEncoder passwordEncoder;

    @BeforeEach
    void setUp() {
        userRepository.deleteAll();

        // ACTIVE 사용자
        User activeUser = User.builder()
                .loginId("test01")
                .password(passwordEncoder.encode("1234")) // ✅ 반드시 인코딩
                .name("테스트유저")
                .email("test01@test.com")
                .phoneNumber("01012345678")
                .userRole(UserRole.USER)
                .recordStatus(RecordStatus.ACTIVE)
                .build();

        // DELETED 사용자
        User deletedUser = User.builder()
                .loginId("deleted01")
                .password(passwordEncoder.encode("1234"))
                .name("삭제유저")
                .userRole(UserRole.USER)
                .recordStatus(RecordStatus.DELETED)
                .build();

        userRepository.save(activeUser);
        userRepository.save(deletedUser);
    }

    @Test
    @DisplayName("로그인 성공: ACTIVE 유저 + 올바른 비밀번호면 200")
    void login_success() throws Exception {
        UserLoginRequest req = new UserLoginRequest("test01", "1234");

        mockMvc.perform(post("/user/login")
                        .contentType("application/json")
                        .content(objectMapper.writeValueAsString(req)))
                .andExpect(status().isOk())
                // ApiResponse 구조에 맞춰서 data.userInfo 같은 경로로 내려가면 경로를 맞춰야 함
                .andExpect(jsonPath("$.data").exists());
    }

    @Test
    @DisplayName("로그인 실패: 비밀번호가 틀리면 4xx(보통 401)")
    void login_fail_wrong_password() throws Exception {
        UserLoginRequest req = new UserLoginRequest("test01", "wrong");

        mockMvc.perform(post("/user/login")
                        .contentType("application/json")
                        .content(objectMapper.writeValueAsString(req)))
                // 현재 exceptionHandling/EntryPoint를 주석처리했으니
                // 401 대신 500이 나올 수도 있음. 이상적으론 401로 맞추는 게 목표.
                .andExpect(status().is4xxClientError());
    }

    @Test
    @DisplayName("로그인 실패: DELETED 유저는 UsernameNotFound로 처리되어 4xx")
    void login_fail_deleted_user() throws Exception {
        UserLoginRequest req = new UserLoginRequest("deleted01", "1234");

        mockMvc.perform(post("/user/login")
                        .contentType("application/json")
                        .content(objectMapper.writeValueAsString(req)))
                .andExpect(status().is4xxClientError());
    }

    @Test
    @DisplayName("로그인 실패: 존재하지 않는 loginId면 4xx")
    void login_fail_not_found() throws Exception {
        UserLoginRequest req = new UserLoginRequest("nope", "1234");

        mockMvc.perform(post("/user/login")
                        .contentType("application/json")
                        .content(objectMapper.writeValueAsString(req)))
                .andExpect(status().is4xxClientError());
    }
}