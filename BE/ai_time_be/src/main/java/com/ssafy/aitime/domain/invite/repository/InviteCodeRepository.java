package com.ssafy.aitime.domain.invite.repository;

import com.ssafy.aitime.domain.invite.entity.InviteCode;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

@Repository
public interface InviteCodeRepository extends JpaRepository<InviteCode, String> {
}
