package com.ssafy.aitime.domain.child.repository;

import com.ssafy.aitime.domain.child.entity.Child;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.UUID;

@Repository
public interface ChildRepository extends JpaRepository<Child, UUID> {
}
