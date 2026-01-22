package com.ssafy.aitime.security.principal;

import com.ssafy.aitime.common.enums.RecordStatus;
import com.ssafy.aitime.domain.user.entity.User;
import com.ssafy.aitime.domain.user.entity.enums.UserRole;
import lombok.Getter;
import org.springframework.security.core.GrantedAuthority;
import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.security.core.userdetails.UserDetails;

import java.util.Collection;
import java.util.List;
import java.util.UUID;

@Getter
public class UserPrincipal implements UserDetails {

    private final UUID userId;
    private final String loginId;
    private final String password;
    private final UserRole userRole;
    private final RecordStatus recordStatus;

    private UserPrincipal(
            UUID userId,
            String loginId,
            String password,
            UserRole userRole,
            RecordStatus recordStatus
    ) {
        this.userId = userId;
        this.loginId = loginId;
        this.password = password;
        this.userRole = userRole;
        this.recordStatus = recordStatus;
    }

    public static UserPrincipal from(User user) {
        return new UserPrincipal(
                user.getUserId(),
                user.getLoginId(),
                user.getPassword(),
                user.getUserRole(),
                user.getRecordStatus()
        );
    }

    /**
     * 권한 부여
     * USER → ROLE_USER
     */
    @Override
    public Collection<? extends GrantedAuthority> getAuthorities() {
        return List.of(
                new SimpleGrantedAuthority("ROLE_" + userRole.name())
        );
    }

    /**
     * Spring Security 기준 username
     */
    @Override
    public String getUsername() {
        return loginId;
    }

    @Override
    public String getPassword() {
        return password;
    }

    /* =====================
       계정 상태 관련
       ===================== */

    @Override
    public boolean isAccountNonExpired() {
        return true;
    }

    @Override
    public boolean isAccountNonLocked() {
        return true;
    }

    @Override
    public boolean isCredentialsNonExpired() {
        return true;
    }

    @Override
    public boolean isEnabled() {
        return recordStatus == RecordStatus.ACTIVE;
    }
}
