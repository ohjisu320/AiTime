import React, { useEffect, useState, useCallback } from 'react';
import { useNavigate, useParams, useBlocker } from 'react-router-dom';
import ConfirmModal from '@/components/common/ConfirmModal';
import ExamBaseLayout from '@/domains/exam/components/layout/ExamBaseLayout';
// import ScreeningGuide from '@/domains/exam/components/Screening/ScreeningGuide';
import { useLiveKitScreening } from '@/domains/exam/hooks/useLiveKitScreening';
import { SCREENING_CONTENT } from '@/domains/exam/constants/missionData';

interface ExamRecordingPageProps {
  missionId?: string;
}

const ExamRecordingPage: React.FC<ExamRecordingPageProps> = ({ missionId: propMissionId }) => {
  const navigate = useNavigate();
  const { missionId: paramMissionId } = useParams<{ missionId: string }>();

  // 1. Props -> 2. Params -> 3. Default 순서로 결정
  const currentMissionId = propMissionId || paramMissionId || "POSE_IMITATION";

  const [isAlertModalOpen, setIsAlertModalOpen] = useState(false);
  const [isPassModalOpen, setIsPassModalOpen] = useState(false);
  // const content = SCREENING_CONTENT[currentMissionId] || SCREENING_CONTENT["POSE_IMITATION"];

  // TODO: 실제 childId는 Context나 props에서 가져와야 함
  const childId = localStorage.getItem('selectedChildId') || 'mock-child-id';

  const handleGoToNextTask = useCallback(() => {
    navigate(`/exam/task/${currentMissionId}`);
  }, [navigate, currentMissionId]);

  // LiveKit 스크리닝 훅
  const {
    videoRef,
    videoStream,
    isAligned,
    volume,
    guideMessage,
    status,
    startScreening,
    stopScreening
  } = useLiveKitScreening();

  // 🚫 뒤로가기/이탈 방지 처리
  const shouldBlock = true;

  useEffect(() => {
    const handleBeforeUnload = (e: BeforeUnloadEvent) => {
      if (shouldBlock) {
        e.preventDefault();
        e.returnValue = '';
      }
    };
    window.addEventListener('beforeunload', handleBeforeUnload);
    return () => window.removeEventListener('beforeunload', handleBeforeUnload);
  }, [shouldBlock]);

  // React Router 네비게이션 방지
  const blocker = useBlocker(shouldBlock);
  const [isBlockerModalOpen, setIsBlockerModalOpen] = useState(false);

  useEffect(() => {
    if (blocker.state === 'blocked') {
      setIsBlockerModalOpen(true);
    } else {
      setIsBlockerModalOpen(false);
    }
  }, [blocker]);

  // 컴포넌트 마운트 시 스크리닝 시작
  useEffect(() => {
    console.log("👀 [ExamRecordingPage] Mounted. ChildId:", childId, "Mission:", currentMissionId);

    if (!childId || childId === 'mock-child-id') {
      console.warn("⚠️ [ExamRecordingPage] Child ID가 없습니다. 로컬 스토리지가 비었거나 mock-child-id입니다.");
    }

    startScreening(childId);
    return () => {
      console.log("👋 [ExamRecordingPage] Unmounting... Stopping screening.");
      stopScreening();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // 상태 변경 로그
  useEffect(() => {
    console.log(`📊 [ExamRecordingPage] Status: ${status}, Stream: ${videoStream ? 'Active' : 'Null'}, Aligned: ${isAligned}, Volume: ${volume}`);
  }, [status, videoStream, isAligned, volume]);

  const handleStartExam = useCallback(() => {
    if (!isAligned || volume > 30) {
      console.log("🚫 [ExamRecordingPage] 준비 미흡 - Aligned:", isAligned, "Volume:", volume);
      setIsAlertModalOpen(true);
      return;
    }
    console.log("✅ [ExamRecordingPage] 테스트 통과!");
    setIsPassModalOpen(true);
  }, [isAligned, volume]);

  return (
    <>
      <ExamBaseLayout
        videoRef={videoRef}
        videoStream={videoStream}
        isRecording={false}
        isAligned={isAligned}
        volume={volume}
        onBack={() => navigate('/exam/mission')}
      >
        {/* AI 가이드 메시지 오버레이 (중앙 하단) */}
        {status === 'screening' && guideMessage && (
          <div className="absolute top-32 left-1/2 transform -translate-x-1/2 bg-black/70 text-white px-6 py-3 rounded-full text-lg font-medium animate-in fade-in slide-in-from-top-5">
            {guideMessage}
          </div>
        )}

        {/* 검사 준비 완료 버튼 (하단 중앙) */}
        <div className="absolute bottom-12 left-1/2 transform -translate-x-1/2 z-50">
          <button
            onClick={handleStartExam}
            disabled={!isAligned || volume > 30}
            className={`
              px-12 py-5 rounded-full font-bold text-xl shadow-2xl transition-all duration-300
              ${isAligned && volume <= 30
                ? "bg-brand-purple text-white hover:scale-105 hover:bg-brand-purple-dark shadow-[0_0_30px_rgba(110,86,207,0.5)]"
                : "bg-gray-500/50 text-gray-300 cursor-not-allowed"}
            `}
          >
            {isAligned && volume <= 30 ? "검사 준비 완료" : "준비 중..."}
          </button>
        </div>
      </ExamBaseLayout>

      {/* 준비 미흡 안내 모달 */}
      <ConfirmModal
        isOpen={isAlertModalOpen}
        onClose={() => setIsAlertModalOpen(false)}
        onConfirm={() => setIsAlertModalOpen(false)}
        title="검사 준비 확인"
        description={
          <div className="text-center space-y-1">
            {!isAligned && <p>아이와 보호자의 얼굴을 가이드에 맞춰주세요.</p>}
            {volume > 30 && <p className="text-rose-500 font-medium">주변 소음이 너무 큽니다. (현재: {volume})</p>}
          </div>
        }
        confirmText="확인"
      />

      {/* 스크리닝 성공 확인 모달 */}
      <ConfirmModal
        isOpen={isPassModalOpen}
        onClose={() => setIsPassModalOpen(false)}
        onConfirm={handleGoToNextTask}
        title="테스트 통과!"
        description="위치와 소음도 측정이 완료되었습니다. 이제 검사가 가능합니다."
        confirmText="검사 시작하기"
      />

      {/* 뒤로가기/이탈 방지 모달 */}
      {blocker.state === 'blocked' && (
        <ConfirmModal
          isOpen={isBlockerModalOpen}
          onClose={() => blocker.reset()}
          onConfirm={() => blocker.proceed()}
          title="검사를 중단하시겠습니까?"
          description="페이지를 이동하면 진행 상황이 저장되지 않습니다."
          confirmText="중단하고 나가기"
          confirmVariant="rose"
        />
      )}
    </>
  );
};

export default ExamRecordingPage;