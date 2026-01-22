package com.ssafy.aitime.security.service;

import com.ssafy.aitime.common.enums.RecordStatus;
import com.ssafy.aitime.domain.user.entity.User;
import com.ssafy.aitime.domain.user.repository.UserRepository;
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

    @Override
    public UserDetails loadUserByUsername(String loginId) throws UsernameNotFoundException {
        User user = userRepository
                .findByLoginIdAndRecordStatus(loginId, RecordStatus.ACTIVE)
                .orElseThrow(() -> new UsernameNotFoundException(loginId));

        return UserPrincipal.from(user);
    }
}
