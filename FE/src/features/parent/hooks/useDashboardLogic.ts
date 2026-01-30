import { useNavigate } from 'react-router-dom';
import { useParentDashboard } from './useParentDashboard';
import type { ChildDashboardStatus } from '../api/dashboardApi';
import { formatDate } from '@/utils/dateFormat';

export interface HeroBannerProps {
    title: string;
    subtitle: string;
    buttonText: string;
    progress: number;
    status: ChildDashboardStatus;
    onPrimaryAction: () => void;
}

interface DashboardCallbacks {
    onNeedHospital?: () => void;
}



export const useDashboardLogic = (callbacks?: DashboardCallbacks) => {
    const navigate = useNavigate();
    const { data, isLoading, isError, refetch } = useParentDashboard();

    // Helper: Calculate D-Day
    const calculateDDay = (targetDate: string | null) => {
        if (!targetDate) return "만료됨";
        const now = new Date();
        const target = new Date(targetDate);
        // Reset time part for accurate day calculation
        now.setHours(0, 0, 0, 0);
        target.setHours(0, 0, 0, 0);

        const diffTime = target.getTime() - now.getTime();
        const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

        if (diffDays < 0) return "만료됨";
        if (diffDays === 0) return "오늘";
        return `D-${diffDays}`;
    };

    // Helper: Determine Hero Content
    const getHeroContent = (): HeroBannerProps => {
        // 1. Safe Fallback
        if (!data) {
            return {
                title: "로딩 중...",
                subtitle: "잠시만 기다려주세요.",
                buttonText: "",
                progress: 0,
                status: 'NEED_HOSPITAL',
                onPrimaryAction: () => { },
            };
        }

        const baseProps = {
            progress: data.examProgress,
            status: data.status,
        };

        // 🚨 중요: 연결된 병원이 없으면 무조건 NEED_HOSPITAL 상태로 처리
        const hasLinkedHospitals = data.linkedHospitals && data.linkedHospitals.length > 0;

        if (!hasLinkedHospitals) {
            return {
                ...baseProps,
                status: 'NEED_HOSPITAL',
                title: "병원을 연결해주세요",
                subtitle: "병원 코드를 입력하고 자녀의 발달 검사를 시작하세요.",
                buttonText: "병원 연결하기",
                onPrimaryAction: callbacks?.onNeedHospital ?? (() => console.warn('onNeedHospital callback not provided')),
            };
        }

        switch (data.status) {
            case 'NEED_HOSPITAL':
            default:
                // 병원 연결이 필요하거나 알 수 없는 상태
                return {
                    ...baseProps,
                    title: "병원을 연결해주세요",
                    subtitle: "병원 코드를 입력하고 자녀의 발달 검사를 시작하세요.",
                    buttonText: "병원 연결하기",
                    onPrimaryAction: callbacks?.onNeedHospital ?? (() => console.warn('onNeedHospital callback not provided')),
                };

            case 'AVAILABLE':
                return {
                    ...baseProps,
                    title: "새 검사 시작하기",
                    subtitle: "아이의 성장 발달을 확인하고 전문적인 분석을 받아보세요.",
                    buttonText: "검사 시작하기",
                    onPrimaryAction: () => navigate('/exam/consent'),
                };

            case 'AVAILABLE_EXPIRED':
                return {
                    ...baseProps,
                    title: "새로운 검사가 필요합니다",
                    subtitle: "이전 검사 데이터가 만료되었습니다. 다시 시작해주세요.",
                    buttonText: "새 검사 시작하기",
                    onPrimaryAction: () => navigate('/exam/consent'),
                };

            case 'IN_PROGRESS':
                const dDay = calculateDDay(data.draftExpiresAt);
                return {
                    ...baseProps,
                    title: `검사 진행 중 (${data.examProgress}/4)`,
                    subtitle: `임시 저장 만료까지 ${dDay} (이어하지 않으면 초기화됩니다)`,
                    buttonText: "검사 이어하기",
                    onPrimaryAction: () => navigate('/exam/consent'),
                };

            case 'COOLDOWN':
            case 'COOLDOWN_BEFORE':
                // data.nextEligibleAt이 존재하는지 확인 (Mock 데이터 작성 시 주의)
                const nextDate = data.nextEligibleAt ? formatDate(data.nextEligibleAt) : "알 수 없음";
                return {
                    ...baseProps,
                    title: "검사가 완료되었습니다",
                    subtitle: `다음 검사 가능일: ${nextDate}`,
                    buttonText: "마지막 검사 영상 보기",
                    onPrimaryAction: () => navigate('/exam/mission'),
                };
        }
    };

    return {
        heroProps: getHeroContent(),
        isLoading,
        isError,
        data,
        refetch,
    };
};

