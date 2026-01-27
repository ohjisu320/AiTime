package com.ssafy.aitime.domain.user.controller;

import com.ssafy.aitime.domain.user.dto.request.PasswordResetRequest;
import com.ssafy.aitime.domain.user.dto.request.UserJoinRequest;
import com.ssafy.aitime.domain.user.dto.request.UserLoginRequest;
import com.ssafy.aitime.domain.user.dto.response.*;
import com.ssafy.aitime.domain.user.entity.enums.UserRole;
import com.ssafy.aitime.domain.user.service.UserService;
import com.ssafy.aitime.domain.user.service.dto.UserInfoDTO;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.webmvc.test.autoconfigure.AutoConfigureMockMvc;
import org.springframework.boot.webmvc.test.autoconfigure.WebMvcTest;
import org.springframework.http.MediaType;
import org.springframework.test.context.bean.override.mockito.MockitoBean;
import org.springframework.test.web.servlet.MockMvc;
import tools.jackson.databind.ObjectMapper;

import java.time.LocalDateTime;
import java.util.UUID;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

@WebMvcTest(UserController.class)
@AutoConfigureMockMvc(addFilters = false) // 시큐리티 필터는 제외하고 API 로직만 테스트
class UserControllerTest {

    @Autowired
    private MockMvc mockMvc;
    @MockitoBean
    private UserService userService;
    @Autowired private ObjectMapper objectMapper;

    @Test
    @DisplayName("로그인 요청 시 AccessToken과 쿠키(Refresh)를 반환한다")
    void loginApiTest() throws Exception {
        // given
        UserLoginRequest request = new UserLoginRequest("testId", "password");
        TokenResponse tokenResponse = new TokenResponse("access-token", "refresh-token",
                new UserInfoDTO(UUID.randomUUID(), "홍길동", UserRole.USER));

        when(userService.login(any())).thenReturn(tokenResponse);

        // when & then
        mockMvc.perform(post("/user/login")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isOk())
                .andExpect(header().exists("Set-Cookie")) // 쿠키 생성 확인
                .andExpect(jsonPath("$.data.accessToken").value("access-token"));
    }

    @Test
    @DisplayName("아이디 중복 확인 요청 시 중복 여부를 반환한다")
    void checkDuplicateApiTest() throws Exception {
        // given
        String loginId = "testUser";
        IdDuplicateResponse response = new IdDuplicateResponse(false);

        // 인자 매칭을 any()로 변경하여 더 유연하게 대응
        when(userService.checkIdDuplicate(any(String.class))).thenReturn(response);

        // when & then
        mockMvc.perform(get("/user/duplicate-id")
                        .param("loginId", loginId) // 파라미터 전달 확인
                        .contentType(MediaType.APPLICATION_JSON))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.status").value("200 OK"))
                .andExpect(jsonPath("$.data.isDuplicate").value(false));
    }

    @Test
    @DisplayName("회원가입 요청 시 유저 정보를 저장하고 201 상태코드를 반환한다")
    void joinApiTest() throws Exception {
        // given
        UserJoinRequest request = new UserJoinRequest(
                "newParent",
                "password123!",
                "홍길동",
                "01012345678",
                true
        );

        UserJoinResponse response = new UserJoinResponse(
                UUID.randomUUID(),
                "newParent",
                "홍길동"
        );

        // userService.join 호출 시 가짜 응답 설정 (실제 SMS 발송 안됨)
        when(userService.join(any(UserJoinRequest.class))).thenReturn(response);

        // when & then
        mockMvc.perform(post("/user/join")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isCreated()) // 201 Created 확인
                .andExpect(jsonPath("$.message").value("회원가입이 성공적으로 완료되었습니다."))
                .andExpect(jsonPath("$.data.loginId").value("newParent"))
                .andExpect(jsonPath("$.data.name").value("홍길동"));
    }

    @Test
    @DisplayName("휴대폰 번호로 아이디 조회 요청 시 아이디와 가입일을 반환한다")
    void getIdApiTest() throws Exception {
        // given
        String phoneNumber = "01012345678";
        IdFindResponse response = new IdFindResponse("testUser123", LocalDateTime.now());

        when(userService.getIdByPhone(anyString())).thenReturn(response);

        // when & then
        mockMvc.perform(get("/user/get-id")
                        .param("phoneNumber", phoneNumber)
                        .contentType(MediaType.APPLICATION_JSON))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.status").value("200 OK"))
                .andExpect(jsonPath("$.message").value("아이디 조회가 완료되었습니다."))
                .andExpect(jsonPath("$.data.loginId").value("testUser123"));
    }

    @Test
    @DisplayName("비밀번호 재설정 전 본인 확인 요청 시 userId를 반환한다")
    void verifyIdentityApiTest() throws Exception {
        // given
        String phoneNumber = "01012345678";
        UUID userId = UUID.randomUUID();
        UserIdentityResponse response = new UserIdentityResponse(true, userId);

        when(userService.verifyUserIdentity(anyString())).thenReturn(response);

        // when & then
        mockMvc.perform(get("/user/verify-identity")
                        .param("phoneNumber", phoneNumber)
                        .contentType(MediaType.APPLICATION_JSON))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.status").value("200 OK"))
                .andExpect(jsonPath("$.data.userId").value(userId.toString()))
                .andExpect(jsonPath("$.data.isVerified").value(true));
    }

    @Test
    @DisplayName("비밀번호 재설정 요청 시 성공 메시지와 변경된 유저 ID를 반환한다")
    void resetPasswordApiTest() throws Exception {
        // given
        UUID userId = UUID.randomUUID();
        PasswordResetRequest request = new PasswordResetRequest(userId, "newPassword123!");
        PasswordResetResponse response = new PasswordResetResponse(userId, LocalDateTime.now());

        when(userService.resetPassword(any(PasswordResetRequest.class))).thenReturn(response);

        // when & then
        mockMvc.perform(patch("/user/password") // PATCH 메서드 사용
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.status").value("200 OK"))
                .andExpect(jsonPath("$.message").value("비밀번호가 성공적으로 변경되었습니다."))
                .andExpect(jsonPath("$.data.userId").value(userId.toString()));
    }
}