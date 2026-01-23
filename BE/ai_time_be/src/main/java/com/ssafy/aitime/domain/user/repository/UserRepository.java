package com.ssafy.aitime.domain.user.repository;

import com.ssafy.aitime.common.enums.RecordStatus;
import com.ssafy.aitime.domain.user.entity.User;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.Optional;
import java.util.UUID;

@Repository
public interface UserRepository extends JpaRepository<User, UUID> {
    // Active인 데이터만 조회
    Optional<User> findByLoginIdAndRecordStatus(String loginId, RecordStatus recordStatus);

    boolean existsByLoginId(String loginId);
}
