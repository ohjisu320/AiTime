package com.ssafy.aitime.security.principal;

import com.ssafy.aitime.common.enums.RecordStatus;
import com.ssafy.aitime.domain.hospital.entity.HospitalStaff;
import com.ssafy.aitime.domain.hospital.entity.enums.StaffRole;
import lombok.Builder;
import lombok.Getter;
import org.springframework.security.core.GrantedAuthority;
import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.security.core.userdetails.UserDetails;

import java.util.Collection;
import java.util.List;
import java.util.UUID;

@Getter
public class HospitalStaffPrincipal implements UserDetails {
    private final UUID hospitalStaffId;
    private final UUID hospitalId;
    private final String loginId;
    private final String password;
    private final String name;
    private final StaffRole staffRole;
    private final RecordStatus recordStatus;

    @Builder
    private HospitalStaffPrincipal(HospitalStaff staff) {
        this.hospitalStaffId = staff.getHospitalStaffId();
        this.hospitalId = staff.getHospital().getHospitalId();
        this.loginId = staff.getLoginId();
        this.password = staff.getPassword();
        this.name = staff.getName();
        this.staffRole = staff.getStaffRole();
        this.recordStatus = staff.getRecordStatus();
    }

    public static HospitalStaffPrincipal from(HospitalStaff staff) {
        return new HospitalStaffPrincipal(staff);
    }

    @Override
    public Collection<? extends GrantedAuthority> getAuthorities() {
        return List.of(new SimpleGrantedAuthority("ROLE_" + staffRole.name()));
    }

    @Override public String getUsername() { return loginId; }
    @Override public String getPassword() { return password; }
    @Override public boolean isEnabled() { return recordStatus == RecordStatus.ACTIVE; }
    @Override public boolean isAccountNonExpired() { return true; }
    @Override public boolean isAccountNonLocked() { return true; }
    @Override public boolean isCredentialsNonExpired() { return true; }
}
