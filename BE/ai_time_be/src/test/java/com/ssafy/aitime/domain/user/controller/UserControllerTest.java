package com.ssafy.aitime.domain.user.controller;

import com.ssafy.aitime.domain.user.dto.request.UserLoginRequest;
import com.ssafy.aitime.domain.user.dto.response.TokenResponse;
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

import java.util.UUID;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
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
}