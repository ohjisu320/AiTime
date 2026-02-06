import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import MissionCard from '@/domains/exam/components/MissionCard';
import ConsentHeader from '@/domains/exam/components/Consent/ConsentHeader';
import InfoNoticeBox from '@/components/common/InfoNoticeBox';
import BigActionButton from '@/components/common/BigActionButton';
import ConfirmModal from '@/components/common/ConfirmModal';
import { startAnalysis } from '@/domains/exam/api/examApi';
import { SCREENING_CONTENT } from '@/domains/exam/constants/missionData';
import { useMissions } from '@/domains/exam/hooks/useMissions';

import Swal from 'sweetalert2';
import MissionReviewModal from '@/domains/exam/components/MissionReviewModal';

const MissionListPage: React.FC = () => {
  const navigate = useNavigate();

  // 로컬 스토리지에서 examId 가져오기 (새로고침/이어하기 대응)
  const examId = localStorage.getItem('currentExamId') || undefined;

  // ✅ useMissions 훅 사용 (중복 선언 제거 및 isUnder18 구조 분해 할당, examStatus 추가)
  const { missions, isLoading, error, isUnder18, examStatus } = useMissions(examId);

  // ✅ 컨텐츠 리졸버 헬퍼
  const getResolvedContent = (videoType: string, isChildUnder18: boolean | null) => {
    if (isChildUnder18 === null) return SCREENING_CONTENT[videoType];

    let resolvedKey = videoType;
    if (videoType === 'POSE_IMITATION' || videoType === 'SPEECH_IMITATION') {
      const suffix = isChildUnder18 ? "_12M" : "_18M";
      resolvedKey = `${videoType}${suffix}`;
    }

    // Fallback if specific key doesn't exist but base key does (though unlikely based on data structure)
    return SCREENING_CONTENT[resolvedKey] || SCREENING_CONTENT[videoType];
  };

  const [recheckModal, setRecheckModal] = useState({ isOpen: false, title: '', type: '', videoId: '' });
  const [submitModalOpen, setSubmitModalOpen] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // 진행도 계산: 모든 미션이 UPLOADED 상태인지 확인 
  const completedCount = missions.filter(t => t.status === 'UPLOADED').length;
  const isAllDone = missions.length > 0 && completedCount === missions.length;

  // 카드 클릭 핸들러 (업로드 상태면 재촬영 모달, 아니면 가이드로 이동) 
  const handleCardClick = (task: any) => {
    if (task.status === 'UPLOADED') {
      setRecheckModal({ isOpen: true, title: task.title, type: task.videoType, videoId: task.videoId });
    } else {
      navigate(`/exam/guide/${task.videoType}`);
    }
  };

  // 재촬영 확정 핸들러 
  const handleRecheckConfirm = () => {
    setRecheckModal({ ...recheckModal, isOpen: false });
    navigate(`/exam/guide/${recheckModal.type}`);
  };

  // 로딩 상태 UI 
  if (isLoading) {
    return (
      <div className="min-h-screen h-screen min-h-[820px] flex items-center justify-center">
        <p className="text-xl font-bold text-gray-400 animate-pulse">검사 진행도를 불러오고 있습니다...</p>
      </div>
    );
  }

  // 에러 상태 UI
  if (error) {
    return (
      <div className="min-h-screen h-screen min-h-[820px] flex items-center justify-center">
        <div className="text-center">
          <p className="text-xl font-bold text-red-500 mb-4">데이터를 불러오는 중 오류가 발생했습니다.</p>
          <p className="text-gray-600">{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="w-full h-screen min-h-[820px] flex flex-col overflow-hidden">
      {/* 🚦 공통 헤더 컴포넌트 사용 */}
      <ConsentHeader
        currentStep={3}
        totalSteps={3}
        onBack={() => navigate('/parent/dashboard')}
        title="검사 미션 선택"
        subtitle={`촬영할 미션을 선택해주세요 (총 ${missions.length}개 미션을 완료해야 합니다)`}
      />

      <main className="flex-1 w-full overflow-y-auto">
        <div className="w-full max-w-[1240px] mx-auto pt-[100px] pb-10 px-6">
          <div className="flex gap-5 items-start">
            <div className="flex flex-col gap-3 flex-1">
              {missions.map((task) => {
                const content = getResolvedContent(task.videoType, isUnder18);
                const cardStatus = task.status === 'UPLOADED' ? 'UPLOADED' : 'PENDING';

                return (
                  <MissionCard
                    key={task.videoType}
                    {...task}
                    title={content?.korTitle || '미션'}
                    subTitle={content?.engTitle}
                    description={content?.description || ''}
                    variant={content?.variant || 'indigo'}
                    status={cardStatus}
                    onClick={() => handleCardClick(task)}
                  />
                );
              })}
            </div>

            <div className="w-[400px] flex flex-col gap-3 sticky top-20">
              <InfoNoticeBox
                title="검사 진행 안내"
                items={[
                  "한 번에 모든 검사를 완료하지 않아도 됩니다.",
                  "촬영 중 문제가 발생하면 언제든 다시 촬영할 수 있습니다.",
                  "모든 검사를 완료하면 AI 분석 리포트를 확인할 수 있습니다."
                ]}
              />
              <BigActionButton
                disabled={!isAllDone || examStatus === 'COMPLETED'}
                onClick={() => setSubmitModalOpen(true)}
                variant="violet"
              >
                {examStatus === 'COMPLETED' ? '리포트 전송 완료' : '리포트 전송하기'}
              </BigActionButton>
            </div>
          </div>
        </div>
      </main>

      {/* 1. 재촬영/확인 모달 */}
      <MissionReviewModal
        isOpen={recheckModal.isOpen}
        title={recheckModal.title}
        examId={localStorage.getItem('examId')}
        videoId={recheckModal.videoId}
        isCompleted={examStatus === 'COMPLETED'}
        onClose={() => setRecheckModal({ ...recheckModal, isOpen: false })}
        onRetake={handleRecheckConfirm}
        onDelete={() => {
          setRecheckModal({ ...recheckModal, isOpen: false });
          window.location.reload();
        }}
      />

      {/* 2. 최종 리포트 제출 모달 */}
      <ConfirmModal
        isOpen={submitModalOpen}
        title={<>완료된 검사리포트를<br />제출합니다.</>}
        description={isSubmitting ? "제출 중입니다..." : "제출 후에는 수정이 불가능합니다."}
        confirmText={isSubmitting ? "제출 중..." : "제출하기"}
        confirmVariant="violet"
        onConfirm={async () => {
          if (isSubmitting) return;

          try {
            const examId = localStorage.getItem('examId');
            if (!examId) {
              Swal.fire('오류', '검사 정보를 찾을 수 없습니다.', 'error');
              return;
            }

            setIsSubmitting(true);

            // ✅ 분석 요청 API 호출
            await startAnalysis(examId);

            navigate('/parent/dashboard'); // 메인 페이지로 이동
          } catch (error) {
            console.error('분석 요청 실패:', error);
            Swal.fire('제출 실패', '분석 요청 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요.', 'error');
          } finally {
            setIsSubmitting(false);
            setSubmitModalOpen(false);
          }
        }}
        onClose={() => !isSubmitting && setSubmitModalOpen(false)}
      />
    </div>
  );
};

export default MissionListPage;