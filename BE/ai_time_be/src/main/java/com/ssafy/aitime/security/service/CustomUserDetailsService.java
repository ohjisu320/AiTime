package com.ssafy.aitime.security.service;

import com.ssafy.aitime.common.enums.RecordStatus;
import com.ssafy.aitime.domain.hospital.repository.HospitalStaffRepository;
import com.ssafy.aitime.domain.user.entity.User;
import com.ssafy.aitime.domain.user.repository.UserRepository;
import com.ssafy.aitime.security.principal.HospitalStaffPrincipal;
import com.ssafy.aitime.security.principal.UserPrincipal;
import lombok.RequiredArgsConstructor;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.security.core.userdetails.UserDetailsService;
import org.springframework.security.core.userdetails.UsernameNotFoundException;
import org.springframework.stereotype.Service;

@Service
@RequiredArgsConstructor
public class CustomUserDetailsService implements UserDetailsService {

    private final UserRepository userRepository;
    private final HospitalStaffRepository hospitalStaffRepository;

    public UserDetails loadUserByLoginIdAndType(String loginId, String type) throws UsernameNotFoundException {
        if ("STAFF".equals(type)) {
            return hospitalStaffRepository.findByLoginIdAndRecordStatus(loginId, RecordStatus.ACTIVE)
                    .map(HospitalStaffPrincipal::from)
                    .orElseThrow(() -> new UsernameNotFoundException("Staff not found: " + loginId));   // TODO: 예외처리 변경
        }

        return userRepository.findByLoginIdAndRecordStatus(loginId, RecordStatus.ACTIVE)
                .map(UserPrincipal::from)
                .orElseThrow(() -> new UsernameNotFoundException("User not found: " + loginId));
    }

    @Override // 기본 시큐리티 호환용
    public UserDetails loadUserByUsername(String loginId) throws UsernameNotFoundException {
        return loadUserByLoginIdAndType(loginId, "USER");
    }
}
