// import { useState, useMemo } from 'react'; // useMemo 제거
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { toast } from "sonner";

// 컴포넌트 임포트
import HeroBanner from '../components/HeroBanner';
import Sidebar from '../components/Sidebar';
import HospitalTimeline from '../components/HospitalTimeline';
import { DashboardSkeleton } from '../components/DashboardSkeleton';
import GuideVideo from '../components/GuideVideo';
import CodeRegisterModal from '../components/CodeRegisterModal';
import ConfirmModal from '../components/ConfirmModal';

// 데이터 및 훅 임포트
import { useDashboardLogic } from '../hooks/useDashboardLogic';
import { registerInviteCode } from '@/features/parent/api/dashboardApi';
import { usePWAInstall } from '@/hooks/usePWAInstall';
import { Download } from 'lucide-react';

const DashboardPage = () => {
    const navigate = useNavigate();

    // 1. Logic Layer: 모든 로직은 훅에서 처리 (콜백 주입)
    const { heroProps, isLoading, isError, data, refetch } = useDashboardLogic({
        onNeedHospital: () => setIsCodeModalOpen(true)
    });

    // PWA Install Hook
    const { isInstallable, installPWA, showIOSInstallGuide, isStandalone } = usePWAInstall();

    // 모달 상태 관리
    const [isModifyModalOpen, setIsModifyModalOpen] = useState(false);
    const [isViewModalOpen, setIsViewModalOpen] = useState(false);
    const [isCodeModalOpen, setIsCodeModalOpen] = useState(false);
    const [isResultLinkModalOpen, setIsResultLinkModalOpen] = useState(false); // 결과 연동 모달
    const [isRegistering, setIsRegistering] = useState(false); // 초대코드 등록 로딩 상태

    // 로딩 중일 때 스켈레톤 UI 표시
    if (isLoading) {
        return (
            <div className="flex w-full h-screen bg-white overflow-hidden">
                <Sidebar childName="로딩 중..." onCodeInputClick={() => { }} />
                <DashboardSkeleton />
            </div>
        );
    }

    // 에러 발생 시 에러 화면 표시
    if (isError || !data) {
        return (
            <div className="flex w-full h-screen bg-white overflow-hidden items-center justify-center">
                <div className="text-center p-8">
                    <h2 className="text-2xl font-bold text-gray-800 mb-4">데이터를 불러올 수 없습니다</h2>
                    <p className="text-gray-600 mb-6">서버 연결에 문제가 있습니다. 잠시 후 다시 시도해주세요.</p>
                    <button
                        onClick={() => refetch()}
                        className="px-6 py-3 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors"
                    >
                        다시 시도
                    </button>
                </div>
            </div>
        );
    }

    // 초대 코드 등록 핸들러
    const handleCodeRegister = async (code: string) => {
        setIsRegistering(true);
        try {
            // [DEBUG] Check data structure for childId
            console.log("Dashboard Data Debug:", data);

            // Use childId from data, fallback to localStorage
            const childId = data?.childId || localStorage.getItem('selectedChildId') || "";
            console.log(`Using childId: ${childId}`);

            if (!childId) {
                toast.error("자녀 정보를 찾을 수 없습니다.");
                return;
            }

            const response = await registerInviteCode(childId, code);

            if (response.code === 200) {
                // 1. 모달 닫기
                setIsCodeModalOpen(false);

                // 2. 데이터 새로고침 (즉시)
                await refetch();

                // 3. 성공 메시지
                toast.success("병원이 연결되었습니다!");

                // 데이터 갱신 후 상태 확인 (결과 연동 제안)
                // Note: refetch returns the *new* data, so accessing `data` state here might still be old
                // unless we await refetch's return or use effect. 
                // However, user requirement is simply "Close -> Refetch -> Toast".
                // I'll keep the logic simple as requested.
            } else {
                // 실패 메시지 (모달 유지)
                toast.error(response.message || "병원 연동에 실패했습니다.");
            }
        } catch (error: any) {
            console.error("Error registering invite code", error);
            // 백엔드 에러 메시지 표시
            const errorMessage = error?.response?.data?.message || "병원 연동 중 오류가 발생했습니다.";
            toast.error(errorMessage);
        } finally {
            setIsRegistering(false);
        }
    };

    const handleResultSubmit = () => {
        // 결과 제출 로직 (현재는 리포트 페이지 이동으로 대체)
        setIsResultLinkModalOpen(false);
        navigate('/parent/report');
    };

    return (
        <div className="flex w-full h-screen bg-white overflow-hidden">
            <Sidebar
                childName={data?.name || "어린이"}
                onCodeInputClick={() => setIsCodeModalOpen(true)}
            />

            <main className="flex-1 overflow-y-auto p-8 flex flex-col gap-8 justify-center relative">

                {/* PWA Install Button (Floating) */}
                <div className="absolute top-6 right-8 z-50">
                    {/* iOS Safari 사용자를 위한 안내 */}
                    {showIOSInstallGuide ? (
                        <div className="flex items-center gap-2 px-4 py-2 rounded-full shadow-lg bg-indigo-600 text-white">
                            <Download size={18} />
                            <span className="text-sm">
                                Safari에서 <strong>공유 → 홈 화면에 추가</strong>를 눌러주세요
                            </span>
                        </div>
                    ) : !isStandalone && (
                        <button
                            onClick={installPWA}
                            disabled={!isInstallable}
                            className={`flex items-center gap-2 px-4 py-2 rounded-full shadow-lg transition-all font-bold 
                                ${isInstallable
                                    ? 'bg-indigo-600 text-white hover:bg-indigo-700 animate-bounce'
                                    : 'bg-gray-200 text-gray-400 cursor-not-allowed'}`}
                            title={isInstallable ? "홈 화면에 추가하기" : "현재 브라우저에서는 설치할 수 없습니다"}
                        >
                            <Download size={18} />
                            {isInstallable ? '홈 화면에 추가하기' : '설치 불가'}
                        </button>
                    )}
                </div>

                {/* HeroBanner */}
                <div className="w-full flex-shrink-0">
                    <HeroBanner {...heroProps} />
                </div>

                <section className="flex flex-col xl:flex-row gap-6 w-full max-w-[1350px]">
                    {/* GuideVideo */}
                    <div className="flex-1 min-h-[450px]">
                        <GuideVideo />
                    </div>

                    {/* HospitalTimeline - 오른쪽 고정 */}
                    <aside className="w-full xl:w-96 flex-none">
                        {data && <HospitalTimeline hospitals={data.linkedHospitals} childName={data.name} onAddClick={() => setIsCodeModalOpen(true)} />}
                    </aside>
                </section>
            </main>

            {/* 수정 모달 (1~3단계) */}
            <ConfirmModal
                isOpen={isModifyModalOpen}
                title="검사 영상을 수정하시겠습니까?"
                description={`현재 ${data?.examProgress}/4 단계 진행 중입니다. 수정 시 기존 분석 데이터는 초기화될 수 있습니다.`}
                confirmText="수정하기"
                onConfirm={() => {
                    setIsModifyModalOpen(false);
                    navigate('/exam/consent');
                }}
                onClose={() => setIsModifyModalOpen(false)}
            />

            {/* 영상 확인 모달 (4단계) */}
            <ConfirmModal
                isOpen={isViewModalOpen}
                title="제출된 영상을 확인하시겠습니까?"
                description="이미 제출된 영상은 수정이나 삭제가 불가능합니다."
                confirmText="영상 확인하기"
                isDestructive={true}
                onConfirm={() => {
                    setIsViewModalOpen(false);
                    navigate('/parent/mission');
                }}
                onClose={() => setIsViewModalOpen(false)}
            />

            {/* 결과 연동 알림 모달 (COOLDOWN_BEFORE) */}
            <ConfirmModal
                isOpen={isResultLinkModalOpen}
                title="이전 검사 결과가 연동되었습니다"
                description={`병원과 연동되어 기존 검사 결과를 제출할 수 있습니다.\n제출하시겠습니까?`}
                confirmText="결과 제출하기"
                onConfirm={handleResultSubmit}
                onClose={() => setIsResultLinkModalOpen(false)}
            />

            {/* 초대 코드 등록 모달 */}
            <CodeRegisterModal
                isOpen={isCodeModalOpen}
                onClose={() => !isRegistering && setIsCodeModalOpen(false)}
                onConfirm={handleCodeRegister}
                title="병원 초대 코드 등록"
                childName={data?.name || "어린이"}
                description="어린이의 검사 결과를 공유받을 병원 초대 코드를 입력해 주세요."
                confirmText="병원 연결하기"
                isLoading={isRegistering}
            />
        </div>
    );
};

export default DashboardPage;