package com.ssafy.aitime.domain.user.repository;

import com.ssafy.aitime.common.enums.RecordStatus;
import com.ssafy.aitime.domain.user.entity.User;
import com.ssafy.aitime.domain.user.entity.enums.UserRole;
import jakarta.persistence.EntityManager;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.data.jpa.test.autoconfigure.DataJpaTest;


import java.util.Optional;

import static org.assertj.core.api.Assertions.assertThat;


@DataJpaTest
class UserRepositoryTest {
    @Autowired
    private UserRepository userRepository;

    @Autowired
    private EntityManager em;

    @Test
    @DisplayName("ACTIVE 유저는 findByLoginIdAndRecordStatus(loginId, ACTIVE)로 조회된다")
    void find_active_user_by_loginId_and_recordStatus() {
        // given
        User user = User.builder()
                .loginId("test01")
                .password("encodedPw")
                .name("테스트유저")
                .email("test01@test.com")
                .phoneNumber("01012345678")
                .userRole(UserRole.USER)
                .recordStatus(RecordStatus.ACTIVE)
                .build();

        userRepository.save(user);
        em.flush();
        em.clear();

        // when
        Optional<User> found = userRepository.findByLoginIdAndRecordStatus("test01", RecordStatus.ACTIVE);

        // then
        assertThat(found).isPresent();
        assertThat(found.get().getLoginId()).isEqualTo("test01");
        assertThat(found.get().getRecordStatus()).isEqualTo(RecordStatus.ACTIVE);
    }

    @Test
    @DisplayName("DELETED 유저는 ACTIVE 조건으로 조회되지 않는다")
    void deleted_user_is_not_found_when_querying_active() {
        // given
        User deletedUser = User.builder()
                .loginId("deleted01")
                .password("encodedPw")
                .name("삭제유저")
                .userRole(UserRole.USER)
                .recordStatus(RecordStatus.DELETED)
                .build();

        userRepository.save(deletedUser);
        em.flush();
        em.clear();

        // when
        Optional<User> found = userRepository.findByLoginIdAndRecordStatus("deleted01", RecordStatus.ACTIVE);

        // then
        assertThat(found).isEmpty();
    }

    @Test
    @DisplayName("DELETED 유저는 DELETED 조건으로 조회된다")
    void deleted_user_is_found_when_querying_deleted() {
        // given
        User deletedUser = User.builder()
                .loginId("deleted02")
                .password("encodedPw")
                .name("삭제유저2")
                .userRole(UserRole.USER)
                .recordStatus(RecordStatus.DELETED)
                .build();

        userRepository.save(deletedUser);
        em.flush();
        em.clear();

        // when
        Optional<User> found = userRepository.findByLoginIdAndRecordStatus("deleted02", RecordStatus.DELETED);

        // then
        assertThat(found).isPresent();
        assertThat(found.get().getRecordStatus()).isEqualTo(RecordStatus.DELETED);
    }
}