import { useEffect } from 'react';
import { useNavigate, Outlet, useLocation } from 'react-router-dom';
import Swal from 'sweetalert2';

interface ExamGuardProps {
    requireExamId?: boolean; // examId가 필요한지 여부 (기본값: true)
    redirectIfExamIdExists?: boolean; // examId가 있으면 리다이렉트 여부 (ConsentPage 등)
}

const ExamGuard = ({ requireExamId = true, redirectIfExamIdExists = false }: ExamGuardProps) => {
    const navigate = useNavigate();
    const location = useLocation();

    useEffect(() => {
        const examId = localStorage.getItem('examId');

        // 1. examId가 필요한 페이지인데 없는 경우 -> 튕겨내기
        if (requireExamId && !examId) {
            Swal.fire({
                title: '잘못된 접근',
                text: '검사 정보가 없습니다. 처음부터 다시 시작해주세요.',
                icon: 'warning',
                confirmButtonText: '확인',
                confirmButtonColor: '#6366F1'
            }).then(() => {
                navigate('/exam/consent', { replace: true });
            });
            return;
        }

        // 2. examId가 있으면 안 되는 페이지(Consent)인데 있는 경우 -> 진행 중인 곳으로 보내기
        // 단, 명시적으로 '처음부터 다시하기' 버튼 등을 누른 경우는 예외 처리가 필요할 수 있음 (현재는 단순 가드)
        if (redirectIfExamIdExists && examId) {
            // 이미 검사 중이면 가이드 페이지로 이동
            // (혹은 Swal 띄우고 이동)
            navigate('/exam/guide', { replace: true });
        }

    }, [navigate, requireExamId, redirectIfExamIdExists, location]);

    return <Outlet />;
};

export default ExamGuard;
