// import { useState, useMemo } from 'react'; // useMemo 추가
import { useState, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';

// 컴포넌트 임포트
import HeroBanner from '../components/HeroBanner';
import Sidebar from '../components/Sidebar';
import HospitalTimeline from '../components/HospitalTimeline';
import LoadingSpinner from '@/components/common/LoadingSpinner';
import GuideVideo from '../components/GuideVideo';
import CodeRegisterModal from '../components/CodeRegisterModal';
import ConfirmModal from '../components/ConfirmModal';

// 데이터 및 훅 임포트
import { useParentDashboard } from '../hooks/useParentDashboard';
import { registerInviteCode } from '@/features/parent/api/dashboardApi'; // Direct import for action

const DashboardPage = () => {
    const navigate = useNavigate();

    // Swagger 데이터를 가져오는 커스텀 훅
    const { data, isLoading, isError, refetch } = useParentDashboard();

    // 모달 상태 관리
    const [isModifyModalOpen, setIsModifyModalOpen] = useState(false);
    const [isViewModalOpen, setIsViewModalOpen] = useState(false);
    const [isCodeModalOpen, setIsCodeModalOpen] = useState(false);


    // 2. 메인 버튼 클릭 핸들러 (순서 중요: bannerProps보다 먼저 정의되어야 함)
    const handleMainButtonClick = () => {
        if (!data) return;

        if (data.linkedHospitals.length === 0) {
            alert("병원 초대 코드를 먼저 등록해 주세요.");
            return;
        }

        if (data.examProgress > 0 && data.examProgress < 4) {
            setIsModifyModalOpen(true);
            return;
        }

        if (data.isExamEligible && data.examProgress === 0) {
            navigate('/exam/consent');
            return;
        }

        if (data.examProgress === 4) {
            setIsViewModalOpen(true);
            return;
        }
    };


    // 3. bannerProps를 함수 내부로 이동 (에러 해결: Cannot find name 'data')
    // useMemo를 사용하면 렌더링 최적화에 도움이 됩니다.
    const bannerProps = useMemo(() => {
        if (!data) return null;
        return {
            isEligible: data.isExamEligible,
            progress: data.examProgress,
            nextDate: data.nextEligibleAt,
            hospitalCount: data.linkedHospitals.length,
            onClick: handleMainButtonClick,
        };
    }, [data]);

    // 로딩 및 에러 처리
    if (isLoading) return <LoadingSpinner />;
    if (isError || !data) return <div className="p-8 text-center">데이터를 불러오는 중 오류가 발생했습니다.</div>;

    // 초대 코드 등록 핸들러
    const handleCodeRegister = async (code: string) => {
        try {
            // TODO: childId should be dynamic
            const response = await registerInviteCode("child-001", code);
            if (response.code === 200) {
                setIsCodeModalOpen(false);
                // 중요: 연동 후 데이터 새로고침 (Soft Refresh)
                await refetch();
            } else {
                alert("병원 연동 실패: " + response.message);
            }
        } catch (error) {
            console.error("Error registering invite code", error);
            alert("병원 연동 중 오류가 발생했습니다.");
        }
    };

    return (
        <div className="flex w-full min-h-[1000px] bg-white overflow-hidden">
            <Sidebar
                childName={data?.name || "어린이"}
                onCodeInputClick={() => setIsCodeModalOpen(true)}
            />

            <main className="flex-1 h-screen overflow-y-auto p-8 flex flex-col gap-8">
                {bannerProps && <HeroBanner {...bannerProps} />}

                <section className="flex flex-col xl:flex-row gap-6 w-full max-w-[1350px]">
                    <div className="flex-1 min-h-[500px]">
                        <GuideVideo />
                    </div>

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
                    navigate('/parent/exam');
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
                    navigate('/parent/report');
                }}
                onClose={() => setIsViewModalOpen(false)}
            />

            {/* 초대 코드 등록 모달 */}
            <CodeRegisterModal
                isOpen={isCodeModalOpen}
                onClose={() => setIsCodeModalOpen(false)}
                onConfirm={handleCodeRegister}
                title="병원 초대 코드 등록"
                childName={data?.name || "어린이"}
                description="어린이의 검사 결과를 공유받을 병원 초대 코드를 입력해 주세요."
                confirmText="병원 연결하기"
            />
        </div>
    );
};

export default DashboardPage;