package com.ssafy.aitime.common.config;

import lombok.Getter;
import lombok.Setter;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.stereotype.Component;

@Getter
@Setter
@Component
@ConfigurationProperties(prefix = "cookie.refresh-token")
public class CookieProperties {
    private String name = "refreshToken";
    private boolean httpOnly = true;
    private boolean secure = false;
    private String sameSite = "Lax";
    private String path = "/";
    private long maxAge = 1209600;  // 14일
}
