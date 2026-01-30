/**
 * JWT 토큰 디코딩 유틸리티
 * 
 * JWT 토큰의 payload 부분을 디코딩하여 사용자 정보를 추출합니다.
 */

export interface JWTPayload {
    sub: string;        // 사용자 ID (username)
    type: string;       // 사용자 타입 (USER, ADMIN 등)
    iat: number;        // 발급 시간
    exp: number;        // 만료 시간
    role: string;       // 역할
    name?: string;      // 사용자 이름 (있을 경우)
}

/**
 * JWT 토큰을 디코딩하여 payload를 반환합니다.
 * @param token - JWT 토큰 문자열
 * @returns 디코딩된 payload 객체 또는 null
 */
export const decodeJWT = (token: string): JWTPayload | null => {
    try {
        // JWT는 "header.payload.signature" 형식
        const parts = token.split('.');

        if (parts.length !== 3) {
            console.error('Invalid JWT format');
            return null;
        }

        // payload 부분 (두 번째 부분) 디코딩
        const payload = parts[1];

        // Base64 URL 디코딩
        const base64 = payload.replace(/-/g, '+').replace(/_/g, '/');
        const jsonPayload = decodeURIComponent(
            atob(base64)
                .split('')
                .map((c) => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
                .join('')
        );

        return JSON.parse(jsonPayload);
    } catch (error) {
        console.error('Failed to decode JWT:', error);
        return null;
    }
};

/**
 * localStorage에서 accessToken을 가져와 디코딩합니다.
 * @returns 디코딩된 payload 또는 null
 */
export const getCurrentUserFromToken = (): JWTPayload | null => {
    const token = localStorage.getItem('accessToken');

    if (!token) {
        console.warn('No access token found in localStorage');
        return null;
    }

    return decodeJWT(token);
};

/**
 * 토큰이 만료되었는지 확인합니다.
 * @param token - JWT 토큰 문자열
 * @returns 만료 여부
 */
export const isTokenExpired = (token: string): boolean => {
    const payload = decodeJWT(token);

    if (!payload || !payload.exp) {
        return true;
    }

    // exp는 초 단위, Date.now()는 밀리초 단위
    return payload.exp * 1000 < Date.now();
};
