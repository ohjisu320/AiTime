import axios from 'axios';

const api = axios.create({
    baseURL: import.meta.env.VITE_API_BASE_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

// Request Interceptor: 자동으로 Authorization 헤더 추가
api.interceptors.request.use(
    (config) => {
        const token = localStorage.getItem('accessToken');
        if (token) {
            config.headers['Authorization'] = `Bearer ${token}`;
        }
        return config;
    },
    (error) => {
        return Promise.reject(error);
    }
);

// Response Interceptor: 401 에러 시 토큰 갱신 시도
let isRefreshing = false;
let failedQueue: any[] = [];

const processQueue = (error: any, token: string | null = null) => {
    failedQueue.forEach(prom => {
        if (error) {
            prom.reject(error);
        } else {
            prom.resolve(token);
        }
    });
    failedQueue = [];
};

api.interceptors.response.use(
    (response) => {
        // 성공 응답은 그대로 반환
        return response;
    },
    async (error) => {
        const originalRequest = error.config;

        // 401 에러이고, 아직 재시도하지 않은 요청인 경우
        if (error.response?.status === 401 && !originalRequest._retry) {
            if (isRefreshing) {
                // 이미 토큰 갱신 중이면 대기열에 추가
                return new Promise((resolve, reject) => {
                    failedQueue.push({ resolve, reject });
                }).then(token => {
                    originalRequest.headers['Authorization'] = `Bearer ${token}`;
                    return api(originalRequest);
                }).catch(err => {
                    return Promise.reject(err);
                });
            }

            originalRequest._retry = true;
            isRefreshing = true;

            const refreshToken = localStorage.getItem('refreshToken');

            if (!refreshToken) {
                // Refresh Token이 없으면 로그인 페이지로 리다이렉트
                console.warn('⚠️ No refresh token available. Redirecting to login...');
                localStorage.removeItem('accessToken');
                localStorage.removeItem('refreshToken');
                localStorage.removeItem('user');
                window.location.href = '/';
                return Promise.reject(error);
            }

            try {
                // Refresh Token으로 새 Access Token 요청
                console.log('🔄 Refreshing access token...');
                const response = await axios.post(
                    `${import.meta.env.VITE_API_BASE_URL}/user/refresh`,
                    { refreshToken }
                );

                if (response.data.code === 200) {
                    const { accessToken: newAccessToken, refreshToken: newRefreshToken } = response.data.data;

                    // 새 토큰 저장
                    localStorage.setItem('accessToken', newAccessToken);
                    if (newRefreshToken) {
                        localStorage.setItem('refreshToken', newRefreshToken);
                    }

                    console.log('✅ Token refreshed successfully');

                    // 대기 중인 요청들 처리
                    processQueue(null, newAccessToken);

                    // 원래 요청 재시도
                    originalRequest.headers['Authorization'] = `Bearer ${newAccessToken}`;
                    return api(originalRequest);
                } else {
                    throw new Error('Token refresh failed');
                }
            } catch (refreshError) {
                console.error('❌ Token refresh failed:', refreshError);
                processQueue(refreshError, null);

                // 토큰 갱신 실패 시 로그아웃 처리
                localStorage.removeItem('accessToken');
                localStorage.removeItem('refreshToken');
                localStorage.removeItem('user');
                window.location.href = '/';
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
