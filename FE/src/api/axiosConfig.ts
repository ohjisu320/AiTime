import axios, { AxiosError, type InternalAxiosRequestConfig } from 'axios';
import type { ApiResponse, ApiError } from './types';

/**
 * Axios 인스턴스 생성
 * Base URL: 환경변수에서 가져옴
 */
const api = axios.create({
    baseURL: import.meta.env.VITE_API_BASE_URL,
    headers: {
        'Content-Type': 'application/json',
    },
    withCredentials: true, // 쿠키 전송을 위해 필요 (refreshToken은 cookie로 관리)
});

// =================================================================
// Request Interceptor: Authorization 헤더 자동 추가
// =================================================================

api.interceptors.request.use(
    (config: InternalAxiosRequestConfig) => {
        const token = localStorage.getItem('accessToken');
        if (token && config.headers) {
            config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
    },
    (error: AxiosError) => {
        return Promise.reject(error);
    }
);

// =================================================================
// Response Interceptor: 401 에러 시 토큰 갱신
// =================================================================

interface QueueItem {
    resolve: (value?: unknown) => void;
    reject: (reason?: unknown) => void;
}

let isRefreshing = false;
let failedQueue: QueueItem[] = [];

/**
 * 대기 중인 요청들을 처리
 */
const processQueue = (error: Error | null = null, token: string | null = null): void => {
    failedQueue.forEach((prom) => {
        if (error) {
            prom.reject(error);
        } else {
            prom.resolve(token);
        }
    });
    failedQueue = [];
};

/**
 * 리프레시 토큰 엔드포인트 결정
 * (로그인된 사용자 타입에 따라 분기)
 */
const getRefreshEndpoint = () => {
    try {
        const userStr = localStorage.getItem('user');
        if (userStr) {
            const userData = JSON.parse(userStr);
            // 병원 관계자(STAFF)인 경우
            if (userData.type === 'STAFF') {
                return '/hospital-staff/refresh';
            }
        }
    } catch (e) {
        console.error('Failed to parse user info for refresh endpoint', e);
    }
    // 기본값: 일반 보호자
    return '/user/refresh';
};

api.interceptors.response.use(
    (response) => {
        // 성공 응답은 그대로 반환
        return response;
    },
    async (error: AxiosError<ApiError>) => {
        const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean };

        // 401 에러이고, 아직 재시도하지 않은 요청인 경우
        if (error.response?.status === 401 && !originalRequest._retry) {
            // 이미 토큰 갱신 중이면 대기열에 추가
            if (isRefreshing) {
                return new Promise((resolve, reject) => {
                    failedQueue.push({ resolve, reject });
                })
                    .then((token) => {
                        if (originalRequest.headers) {
                            originalRequest.headers.Authorization = `Bearer ${token}`;
                        }
                        return api(originalRequest);
                    })
                    .catch((err) => {
                        return Promise.reject(err);
                    });
            }

            originalRequest._retry = true;
            isRefreshing = true;

            try {
                const refreshEndpoint = getRefreshEndpoint();
                console.log(`🔄 Refreshing access token via ${refreshEndpoint}...`);

                // Refresh Token으로 새 Access Token 요청 (Body 전송)
                const response = await axios.post(
                    `${import.meta.env.VITE_API_BASE_URL}${refreshEndpoint}`,
                    { refreshToken }
                );

                if (response.data.code === 200 && response.data.data) {
                    const { accessToken: newAccessToken } = response.data.data;

                    // 새 Access Token 저장
                    localStorage.setItem('accessToken', newAccessToken);
                    console.log('✅ Token refreshed successfully');

                    // 대기 중인 요청들 처리
                    processQueue(null, newAccessToken);

                    // 원래 요청 재시도
                    if (originalRequest.headers) {
                        originalRequest.headers.Authorization = `Bearer ${newAccessToken}`;
                    }
                    return api(originalRequest);
                } else {
                    throw new Error('Token refresh failed: Invalid response');
                }
            } catch (refreshError) {
                console.error('❌ Token refresh failed:', refreshError);
                processQueue(refreshError as Error, null);

                // 토큰 갱신 실패 시 로그아웃 처리
                handleLogout();
                return Promise.reject(refreshError);
            } finally {
                isRefreshing = false;
            }
        }

        // 401이 아닌 다른 에러는 그대로 반환
        return Promise.reject(error);
    }
);

export default api;
