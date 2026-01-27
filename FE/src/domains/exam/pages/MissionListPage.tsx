import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import MissionCard from '../components/MissionCard';
import MissionInfoBox from '../components/MissionSide/MissionInfoBox';
import ReportButton from '../components/MissionSide/ReportButton';
import ConfirmModal from '@/components/common/ConfirmModal';

const MissionListPage: React.FC = () => {
    const navigate = useNavigate();

// 1. 재촬영 모달 상태
  const [recheckModal, setRecheckModal] = useState({ isOpen: false, title: '', type: '' });
  // 2. 최종 제출 모달 상태
  const [submitModalOpen, setSubmitModalOpen] = useState(false);

  // 재촬영 '예' 눌렀을 때 실행될 함수 ConfirmModal
  const handleRecheckConfirm = () => {
    const missionNumber = recheckModal.type.replace('TASK', '');
    setRecheckModal({ ...recheckModal, isOpen: false });
    navigate(`/exam/guide/${missionNumber}`); // 가이드로 이동 ConfirmModal
  };

  // 리포트 제출 '네' 눌렀을 때 실행될 함수 ConfirmModal
  const handleReportSubmit = () => {
    setSubmitModalOpen(false);
    navigate('/exam/success'); // 성공 페이지로 이동 ConfirmModal
  };
    // API 명세 Mock 데이터 (모두 UPLOADED로 설정하여 테스트 가능)
    const videoTasks = [
        { type: 'TASK1', title: '이름 부르기 반응', subTitle: 'Name Response', desc: '아이의 이름을 불러 눈맞춤과 반응을 관찰합니다', variant: 'pink', status: 'UPLOADED' },
        { type: 'TASK2', title: '사물 가리키기', subTitle: 'Object Pointing', desc: '"공 어디 있어?" 같은 질문에 가리키는 행동을 관찰합니다', variant: 'amber', status: 'PENDING' },
        { type: 'TASK3', title: '간단한 지시 따르기', subTitle: 'Simple Commands', desc: '"공 가져와", "앉아" 같은 간단한 지시를 따르는지 관찰합니다', variant: 'emerald', status: 'PENDING' },
        { type: 'TASK4', title: '자유 놀이 관찰', subTitle: 'Free Play', desc: '장난감과 자유롭게 놀 때의 행동 패턴을 관찰합니다', variant: 'violet', status: 'UPLOADED' },
    ];

    const completedCount = videoTasks.filter(t => t.status === 'UPLOADED').length;
    const isAllDone = completedCount === videoTasks.length;

    // MissionListPage.tsx의 로직 확인
    const handleCardClick = (task: typeof videoTasks[0]) => {
        if (task.status === 'UPLOADED') {
            // 이 로그가 터미널이나 콘솔에 찍히는지 확인해보세요.
            console.log("모달 오픈 대상:", task.title);
            setRecheckModal({ isOpen: true, title: task.title, type: task.type });
        } else {
            navigate(`/exam/recorder/${task.type.toLowerCase()}`);
        }
    };
    const handleSubmit = () => {
        if (isAllDone) setSubmitModalOpen(true); // alert 대신 커스텀 모달 오픈
    };

    return (
        <div className="min-h-screen bg-gradient-to-b from-gray-50 to-slate-100 pb-20 overflow-x-hidden">
            <main className="max-w-[1240px] mx-auto mt-32 px-6">
                <div className="text-center mb-16">
                    <h1 className="text-4xl font-extrabold text-gray-900 mb-4 tracking-tight">검사 미션 선택</h1>
                    <p className="text-xl text-gray-500 font-medium">촬영할 미션을 선택해주세요 (총 4개 미션을 완료해야 합니다)</p>
                </div>

                <div className="flex gap-10 items-start">
                    <div className="flex flex-col gap-6 flex-1">
                        {videoTasks.map((task) => (
                            <MissionCard
                                key={task.type}
                                title={task.title}
                                subTitle={task.subTitle}
                                description={task.desc}
                                variant={task.variant as 'pink' | 'purple' | 'blue' | 'emerald' | 'amber' | 'violet'}
                                status={task.status as 'PENDING' | 'UPLOADED'}
                                onClick={() => handleCardClick(task)}
                            />
                        ))}
                    </div>



                    <div className="w-[480px] flex flex-col gap-6 sticky top-32">
                        <MissionInfoBox />
                        <ReportButton isAllDone={isAllDone} onSend={handleSubmit} />
                    </div>
                </div>
            </main>

            {/* ⚠️ 재촬영 확인 모달 */}
            <ConfirmModal
                isOpen={recheckModal.isOpen}
                title={<>{recheckModal.title} 검사를<br />다시 진행하시겠습니까?</>}
                confirmVariant="slate" // 재촬영은 조금 차분한 색으로 ConfirmModal
                onConfirm={handleRecheckConfirm}
                onClose={() => setRecheckModal({ ...recheckModal, isOpen: false })}
            />

            {/* 🚀 최종 리포트 제출 모달 (분리 완료) ConfirmModal */}
            <ConfirmModal
                isOpen={submitModalOpen}
                title={<>완료된 검사리포트를<br />제출합니다.</>}
                confirmVariant="violet" // 제출은 강조되는 보라색으로 ConfirmModal
                onConfirm={handleReportSubmit}
                onClose={() => setSubmitModalOpen(false)}
            />
        </div>
    );
};

export default MissionListPage;