import axios from 'axios';

const api = axios.create({
    baseURL: import.meta.env.VITE_API_BASE_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

api.interceptors.request.use(
    (config) => {
        // [TEST] Dashboard API currently uses manual header injection, 
        // but this interceptor is kept for global token logic if needed later.
        const token = localStorage.getItem('accessToken');
        if (token) {
            config.headers['Authorization'] = `Bearer ${token}`;
        }
        console.log('API Request Header:', config.headers);
        return config;
    },
    (error) => {
        return Promise.reject(error);
    }
);

export default api;
