import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import MissionCard from '../components/MissionCard';
import InfoNoticeBox from '@/components/common/InfoNoticeBox';
import BigActionButton from '@/components/common/BigActionButton';
import ConfirmModal from '@/components/common/ConfirmModal';
import { useMissions } from '../hooks/useMissions'; // 👈 훅 임포트 

const MissionListPage: React.FC = () => {
  const navigate = useNavigate();
  const { missions, isLoading } = useMissions(); // 👈 데이터 호출 

  const [recheckModal, setRecheckModal] = useState({ isOpen: false, title: '', type: '' });
  const [submitModalOpen, setSubmitModalOpen] = useState(false);

  // 진행도 계산 
  const completedCount = missions.filter(t => t.status === 'UPLOADED').length;
  const isAllDone = missions.length > 0 && completedCount === missions.length;

  const handleCardClick = (task: any) => {
    const missionNumber = task.videoType.replace('TASK', '');
    if (task.status === 'UPLOADED') {
      setRecheckModal({ isOpen: true, title: task.title, type: task.videoType });
    } else {
      navigate(`/exam/guide/${missionNumber}`);
    }
  };

  const handleRecheckConfirm = () => {
    const missionNumber = recheckModal.type.replace('TASK', '');
    setRecheckModal({ ...recheckModal, isOpen: false });
    navigate(`/exam/guide/${missionNumber}`);
  };

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p className="text-xl font-bold text-gray-400 animate-pulse">검사 진행도를 불러오고 있습니다...</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-50 to-slate-100 pb-20">
      <main className="max-w-[1240px] mx-auto mt-32 px-6">
        <div className="text-center mb-16">
          <h1 className="text-4xl font-extrabold text-gray-900 mb-4 tracking-tight">검사 미션 선택</h1>
          <p className="text-xl text-gray-500 font-medium">촬영할 미션을 선택해주세요 (총 {missions.length}개 미션을 완료해야 합니다)</p>
        </div>

        <div className="flex gap-10 items-start">
          <div className="flex flex-col gap-6 flex-1">
            {missions.map((task) => (
              <MissionCard
                key={task.videoType}
                {...task}
                // 타입 안정성 확보 
                status={task.status as 'UPLOADED' | 'PENDING'}
                variant={task.variant as any}
                onClick={() => handleCardClick(task)}
              />
            ))}
          </div>

          <div className="w-[480px] flex flex-col gap-6 sticky top-32">
            <InfoNoticeBox
              title="검사 진행 안내"
              items={[
                "한 번에 모든 검사를 완료하지 않아도 됩니다.",
                "촬영 중 문제가 발생하면 언제든 다시 촬영할 수 있습니다.",
                "모든 검사를 완료하면 AI 분석 리포트를 확인할 수 있습니다."
              ]}
            />
            <BigActionButton
              disabled={!isAllDone}
              onClick={() => setSubmitModalOpen(true)}
              variant="violet"
            >
              리포트 전송하기
            </BigActionButton>
          </div>
        </div>
      </main>

      <ConfirmModal
        isOpen={recheckModal.isOpen}
        title={<>{recheckModal.title} 검사를<br />다시 진행하시겠습니까?</>}
        confirmVariant="slate"
        onConfirm={handleRecheckConfirm}
        onClose={() => setRecheckModal({ ...recheckModal, isOpen: false })}
      />

      <ConfirmModal
        isOpen={submitModalOpen}
        title={<>완료된 검사리포트를<br />제출합니다.</>}
        confirmVariant="violet"
        onConfirm={() => navigate('/exam/success')}
        onClose={() => setSubmitModalOpen(false)}
      />
    </div>
  );
};

export default MissionListPage;