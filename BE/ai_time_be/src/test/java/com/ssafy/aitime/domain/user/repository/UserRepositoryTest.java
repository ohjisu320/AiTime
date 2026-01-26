package com.ssafy.aitime.domain.user.repository;

import com.ssafy.aitime.common.enums.RecordStatus;
import com.ssafy.aitime.domain.user.entity.User;
import com.ssafy.aitime.domain.user.entity.enums.UserRole;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.data.jpa.test.autoconfigure.DataJpaTest;

import java.util.Optional;

import static org.assertj.core.api.AssertionsForClassTypes.assertThat;
import static org.junit.jupiter.api.Assertions.*;

@DataJpaTest
class UserRepositoryTest {
    @Autowired
    private UserRepository userRepository;

    @Test
    @DisplayName("로그인 ID와 ACTIVE 상태로 사용자를 조회한다")
    void findByLoginIdAndRecordStatus_Success() {
        // given
        User user = User.builder()
                .loginId("ssafy123")
                .password("password!")
                .name("김싸피")
                .userRole(UserRole.USER)
                .recordStatus(RecordStatus.ACTIVE)
                .build();
        userRepository.save(user);

        // when
        Optional<User> foundUser = userRepository.findByLoginIdAndRecordStatus("ssafy123", RecordStatus.ACTIVE);

        // then
        assertThat(foundUser).isPresent();
        assertThat(foundUser.get().getLoginId()).isEqualTo("ssafy123");
        assertThat(foundUser.get().getRecordStatus()).isEqualTo(RecordStatus.ACTIVE);
    }

    @Test
    @DisplayName("사용자 상태가 DELETED인 경우 조회되지 않아야 한다")
    void findByLoginIdAndRecordStatus_Fail_WhenDeleted() {
        // given
        User user = User.builder()
                .loginId("deletedUser")
                .password("password!")
                .name("탈퇴자")
                .userRole(UserRole.USER)
                .recordStatus(RecordStatus.DELETED)
                .build();
        userRepository.save(user);

        // when: ACTIVE 상태로 조회 시도
        Optional<User> foundUser = userRepository.findByLoginIdAndRecordStatus("deletedUser", RecordStatus.ACTIVE);

        // then
        assertThat(foundUser).isEmpty();
    }

    @Test
    @DisplayName("로그인 ID 중복 여부를 확인한다")
    void existsByLoginId_Success() {
        // given
        User user = User.builder()
                .loginId("existUser")
                .password("password!")
                .name("기존유저")
                .userRole(UserRole.USER)
                .build();
        userRepository.save(user);

        // when
        boolean exists = userRepository.existsByLoginId("existUser");
        boolean notExists = userRepository.existsByLoginId("newUser");

        // then
        assertThat(exists).isTrue();
        assertThat(notExists).isFalse();
    }

    @Test
    @DisplayName("유저 ID와 ACTIVE 상태로 사용자를 조회한다")
    void findByUserIdAndRecordStatus_Success() {
        // given
        User user = User.builder()
                .loginId("userIdTest")
                .password("password!")
                .name("ID테스트")
                .recordStatus(RecordStatus.ACTIVE)
                .build();
        User savedUser = userRepository.save(user);

        // when
        Optional<User> foundUser = userRepository.findByUserIdAndRecordStatus(savedUser.getUserId(), RecordStatus.ACTIVE);

        // then
        assertThat(foundUser).isPresent();
        assertThat(foundUser.get().getUserId()).isEqualTo(savedUser.getUserId());
        assertThat(foundUser.get().getRecordStatus()).isEqualTo(RecordStatus.ACTIVE);
    }

    @Test
    @DisplayName("핸드폰 번호와 ACTIVE 상태로 사용자를 조회한다")
    void findByPhoneNumberAndRecordStatus_Success() {
        // given
        String phone = "01099998888";
        User user = User.builder()
                .loginId("phoneTest")
                .password("password!")
                .name("폰테스트")
                .phoneNumber(phone)
                .recordStatus(RecordStatus.ACTIVE)
                .build();
        userRepository.save(user);

        // when
        Optional<User> foundUser = userRepository.findByPhoneNumberAndRecordStatus(phone, RecordStatus.ACTIVE);

        // then
        assertThat(foundUser).isPresent();
        assertThat(foundUser.get().getPhoneNumber()).isEqualTo(phone);
        assertThat(foundUser.get().getRecordStatus()).isEqualTo(RecordStatus.ACTIVE);
    }

    @Test
    @DisplayName("핸드폰 번호가 같더라도 DELETED 상태라면 조회되지 않아야 한다")
    void findByPhoneNumberAndRecordStatus_Fail_WhenDeleted() {
        // given
        String phone = "01011112222";
        User user = User.builder()
                .loginId("deletedPhoneUser")
                .password("password!")
                .name("삭제유저")
                .phoneNumber(phone)
                .recordStatus(RecordStatus.DELETED)
                .build();
        userRepository.save(user);

        // when
        Optional<User> foundUser = userRepository.findByPhoneNumberAndRecordStatus(phone, RecordStatus.ACTIVE);

        // then
        assertThat(foundUser).isEmpty();
    }
}