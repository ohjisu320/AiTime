package com.ssafy.aitime.infra.swagger;

import io.swagger.v3.oas.models.Components;
import io.swagger.v3.oas.models.OpenAPI;
import io.swagger.v3.oas.models.info.Info;
import io.swagger.v3.oas.models.security.SecurityRequirement;
import io.swagger.v3.oas.models.security.SecurityScheme;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
public class SwaggerConfig {

    @Bean
    public OpenAPI customOpenAPI() {
        String securitySchemeName = "Bearer Authentication";

        return new OpenAPI()
                .info(new Info()
                        .title("AI Time API")
                        .version("1.0.0")
                        .description("의사 예약 관리 시스템 API"))

                // JWT 보안 스키마 정의
                .components(new Components()
                        .addSecuritySchemes(securitySchemeName,
                                new SecurityScheme()
                                        .name(securitySchemeName)
                                        .type(SecurityScheme.Type.HTTP)
                                        .scheme("bearer")
                                        .bearerFormat("JWT")
                                        .in(SecurityScheme.In.HEADER)
                                        .description("JWT 토큰을 입력하세요 (Bearer 제외)")
                        )
                )

                // 전역 보안 요구사항
                .addSecurityItem(new SecurityRequirement()
                        .addList(securitySchemeName));
    }
}