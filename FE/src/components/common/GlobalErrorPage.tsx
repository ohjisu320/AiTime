import { useRouteError, useNavigate } from 'react-router-dom';
import { AlertCircle, Home } from 'lucide-react';

const GlobalErrorPage = () => {
    const error = useRouteError() as any;
    const navigate = useNavigate();

    // 에러 메시지 추출
    let errorMessage = "요청을 처리하는 중 문제가 발생했습니다.";

    if (error) {
        if (error.message) {
            errorMessage = error.message;
        } else if (error.statusText) {
            errorMessage = error.statusText;
        } else if (typeof error === 'string') {
            errorMessage = error;
        }
    }

    // 로그인 상태 및 role 확인
    const getHomeUrl = () => {
        const accessToken = localStorage.getItem('accessToken');

        // 로그인 안한 상태
        if (!accessToken) {
            // 현재 경로 확인 - staff 페이지였는지 확인
            const currentPath = window.location.pathname;
            if (currentPath.startsWith('/doctor') || currentPath.startsWith('/reception')) {
                return '/staff-login'; // STAFF 로그인 페이지
            }
            return '/'; // PARENT 로그인 페이지
        }

        // 로그인한 상태 - user 객체에서 type/staffRole 확인
        const userStr = localStorage.getItem('user');
        if (!userStr) {
            // user 정보는 없지만 토큰은 있음 → 경로로 판단
            const currentPath = window.location.pathname;
            if (currentPath.startsWith('/doctor') || currentPath.startsWith('/reception')) {
                return '/staff-login';
            }
            return '/';
        }

        try {
            const user = JSON.parse(userStr);
            const userType = user.type; // 'PARENT' or 'STAFF'

            // PARENT 계정
            if (userType === 'PARENT') {
                return '/parent/dashboard';
            }

            // STAFF 계정 (DOCTOR 또는 DESK)
            if (userType === 'STAFF') {
                const staffRole = user.staffRole; // 'DOCTOR' or 'DESK'

                if (staffRole === 'DOCTOR') {
                    return '/doctor/dashboard';
                } else if (staffRole === 'DESK') {
                    return '/reception/dashboard';
                }
            }

            // 알 수 없는 타입 - 경로로 판단
            const currentPath = window.location.pathname;
            if (currentPath.startsWith('/doctor') || currentPath.startsWith('/reception')) {
                return '/staff-login';
            }
            return '/';
        } catch (error) {
            console.error('Failed to parse user data:', error);
            // 파싱 실패 - 경로로 판단
            const currentPath = window.location.pathname;
            if (currentPath.startsWith('/doctor') || currentPath.startsWith('/reception')) {
                return '/staff-login';
            }
            return '/';
        }
    };

    const homeUrl = getHomeUrl();
    const buttonText = homeUrl === '/' ? '로그인 페이지로 이동' : homeUrl === '/staff-login' ? '직원 로그인 페이지로 이동' : '홈으로 이동';

    return (
        <div className="min-h-screen h-screen flex items-center justify-center bg-[#E3E0F5]">
            <div className="max-w-md w-full mx-auto px-6">
                <div className="bg-white rounded-[40px] shadow-[0px_10px_40px_rgba(149,147,217,0.3)] p-10 text-center">
                    {/* 에러 아이콘 */}
                    <div className="mb-6 flex justify-center">
                        <div className="w-20 h-20 bg-red-100 rounded-full flex items-center justify-center">
                            <AlertCircle className="w-12 h-12 text-red-600" />
                        </div>
                    </div>

                    {/* 에러 메시지 */}
                    <h1 className="text-2xl font-bold text-[#1A1A1A] mb-3">
                        페이지 오류
                    </h1>
                    <p className="text-gray-500 mb-8 whitespace-pre-line">
                        {errorMessage}
                    </p>

                    {/* 홈으로 이동 버튼 */}
                    <button
                        onClick={() => navigate(homeUrl)}
                        className="w-full h-14 bg-[#9593D9] hover:bg-[#7B78C5] text-white font-bold rounded-xl transition-all shadow-lg shadow-[#9593D9]/25 flex items-center justify-center gap-2 text-lg"
                    >
                        <Home className="w-5 h-5" />
                        <span>{buttonText}</span>
                    </button>
                </div>

                {/* 추가 안내 텍스트 */}
                <p className="text-center text-sm text-gray-400 mt-6">
                    문제가 계속되면 고객센터로 문의해주세요.
                </p>
            </div>
        </div>
    );
};

export default GlobalErrorPage;
