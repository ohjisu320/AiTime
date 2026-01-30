/**
 * Production API 연결 테스트 유틸리티
 * 
 * 배포 환경에서 API 서버 연결 상태를 확인하기 위한 테스트 함수입니다.
 * CORS, Mixed Content, 네트워크 연결 등의 문제를 진단합니다.
 * 
 * 사용법:
 * 1. App.tsx나 main.tsx에서 import
 * 2. useEffect나 컴포넌트 마운트 시 testProductionAPI() 호출
 * 3. 브라우저 콘솔(F12)에서 결과 확인
 */

interface TestResult {
    success: boolean;
    message: string;
    details?: any;
    error?: any;
}

/**
 * Production API 서버 연결 테스트
 * @param baseUrl - 테스트할 API 서버 주소 (기본값: 환경변수에서 가져옴)
 */
export const testProductionAPI = async (baseUrl?: string): Promise<void> => {
    const apiUrl = baseUrl || import.meta.env.VITE_API_BASE_URL;
    const envMode = import.meta.env.VITE_ENV_MODE || import.meta.env.MODE;

    console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
    console.log('🔍 Production API 연결 테스트 시작');
    console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
    console.log('📍 환경:', envMode);
    console.log('🌐 API URL:', apiUrl);
    console.log('🕐 테스트 시작 시간:', new Date().toLocaleString('ko-KR'));
    console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n');

    // 1. 프로토콜 체크 (Mixed Content 검증)
    checkProtocol(apiUrl);

    // 2. Health Check 엔드포인트 테스트
    await testHealthCheck(apiUrl);

    // 3. 인증이 필요한 엔드포인트 테스트 (옵션)
    await testAuthenticatedEndpoint(apiUrl);

    console.log('\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
    console.log('✅ Production API 연결 테스트 완료');
    console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n');
};

/**
 * 프로토콜 검증 (HTTPS/HTTP Mixed Content 체크)
 */
const checkProtocol = (apiUrl: string): void => {
    const currentProtocol = window.location.protocol;
    const apiProtocol = apiUrl.startsWith('https') ? 'https:' : 'http:';

    console.log('🔒 [프로토콜 체크]');
    console.log('   현재 페이지:', currentProtocol);
    console.log('   API 서버:', apiProtocol);

    if (currentProtocol === 'https:' && apiProtocol === 'http:') {
        console.warn('⚠️  경고: Mixed Content 문제 발생 가능!');
        console.warn('   HTTPS 페이지에서 HTTP API를 호출하면 브라우저가 차단할 수 있습니다.');
        console.warn('   해결책: API 서버도 HTTPS를 사용하거나, 프록시 설정이 필요합니다.');
    } else {
        console.log('✅ 프로토콜 일치 - Mixed Content 문제 없음\n');
    }
};

/**
 * Health Check 엔드포인트 테스트
 */
const testHealthCheck = async (apiUrl: string): Promise<void> => {
    console.log('🏥 [Health Check 테스트]');

    // 일반적인 Health Check 엔드포인트들
    const healthEndpoints = [
        '/health',
        '/actuator/health',
        '/api/health',
        '/',
    ];

    for (const endpoint of healthEndpoints) {
        const testUrl = `${apiUrl}${endpoint}`;
        console.log(`   시도 중: ${testUrl}`);

        try {
            const startTime = performance.now();
            const response = await fetch(testUrl, {
                method: 'GET',
                mode: 'cors',
                headers: {
                    'Accept': 'application/json',
                },
            });
            const endTime = performance.now();
            const responseTime = (endTime - startTime).toFixed(2);

            if (response.ok) {
                const data = await response.json().catch(() => response.text());
                console.log(`   ✅ 성공! (${response.status}) - ${responseTime}ms`);
                console.log('   응답:', data);
                return; // 성공하면 종료
            } else {
                console.log(`   ❌ 실패: ${response.status} ${response.statusText}`);
            }
        } catch (error: any) {
            console.log(`   ❌ 에러:`, error.message);

            // CORS 에러 상세 분석
            if (error.message.includes('CORS') || error.message.includes('NetworkError')) {
                console.error('   🚨 CORS 에러 발생!');
                console.error('   원인: 서버에서 CORS 헤더를 제대로 설정하지 않았을 가능성');
                console.error('   필요한 헤더:');
                console.error('     - Access-Control-Allow-Origin: *');
                console.error('     - Access-Control-Allow-Methods: GET, POST, PUT, DELETE');
                console.error('     - Access-Control-Allow-Headers: Content-Type, Authorization');
            }
        }
    }

    console.log('   ⚠️  모든 Health Check 엔드포인트 실패\n');
};

/**
 * 인증이 필요한 엔드포인트 테스트
 */
const testAuthenticatedEndpoint = async (apiUrl: string): Promise<void> => {
    console.log('🔐 [인증 엔드포인트 테스트]');

    const token = localStorage.getItem('accessToken');

    if (!token) {
        console.log('   ⚠️  localStorage에 accessToken이 없습니다.');
        console.log('   인증이 필요한 API 테스트를 건너뜁니다.\n');
        return;
    }

    console.log('   토큰 발견:', token.substring(0, 20) + '...');

    // 실제 사용 중인 엔드포인트 테스트
    const testEndpoint = '/child/test-child-id'; // 실제 childId로 교체 가능
    const testUrl = `${apiUrl}${testEndpoint}`;

    console.log(`   시도 중: ${testUrl}`);

    try {
        const startTime = performance.now();
        const response = await fetch(testUrl, {
            method: 'GET',
            mode: 'cors',
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`,
            },
        });
        const endTime = performance.now();
        const responseTime = (endTime - startTime).toFixed(2);

        console.log(`   응답 상태: ${response.status} ${response.statusText} (${responseTime}ms)`);

        if (response.ok) {
            const data = await response.json();
            console.log('   ✅ 인증 성공!');
            console.log('   응답 데이터:', data);
        } else if (response.status === 401) {
            console.log('   ❌ 인증 실패: 토큰이 만료되었거나 유효하지 않습니다.');
            const errorData = await response.json().catch(() => null);
            if (errorData) {
                console.log('   에러 상세:', errorData);
            }
        } else if (response.status === 404) {
            console.log('   ⚠️  엔드포인트를 찾을 수 없습니다. (정상일 수 있음)');
        } else {
            const errorData = await response.json().catch(() => response.text());
            console.log('   ❌ 에러:', errorData);
        }
    } catch (error: any) {
        console.error('   ❌ 요청 실패:', error.message);

        if (error.message.includes('CORS')) {
            console.error('   🚨 CORS 에러: 서버 설정을 확인하세요.');
        } else if (error.message.includes('NetworkError')) {
            console.error('   🚨 네트워크 에러: 서버가 응답하지 않거나 방화벽에 차단되었을 수 있습니다.');
        }
    }

    console.log('');
};

/**
 * 간단한 테스트 (axios 사용)
 * axios가 설치되어 있는 경우 사용 가능
 */
export const testWithAxios = async (baseUrl?: string): Promise<void> => {
    try {
        const axios = (await import('axios')).default;
        const apiUrl = baseUrl || import.meta.env.VITE_API_BASE_URL;

        console.log('🔧 [Axios 테스트]');
        console.log('   API URL:', apiUrl);

        const response = await axios.get(`${apiUrl}/health`, {
            timeout: 5000,
        });

        console.log('   ✅ Axios 테스트 성공!');
        console.log('   응답:', response.data);
    } catch (error: any) {
        console.error('   ❌ Axios 테스트 실패:', error.message);
        if (error.response) {
            console.error('   상태 코드:', error.response.status);
            console.error('   응답 데이터:', error.response.data);
        }
    }
};

// 기본 export
export default testProductionAPI;
