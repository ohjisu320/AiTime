import React, { useEffect, useState, useCallback } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import ConfirmModal from '@/components/common/ConfirmModal';
import ExamBaseLayout from '../components/layout/ExamBaseLayout';
import ScreeningGuide from '../components/Screening/ScreeningGuide';
import { useLiveKitScreening } from '../hooks/useLiveKitScreening';
import { SCREENING_CONTENT } from '../constants/missionData';

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
  const content = SCREENING_CONTENT[currentMissionId] || SCREENING_CONTENT["POSE_IMITATION"];

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

  // 컴포넌트 마운트 시 스크리닝 시작
  useEffect(() => {
    startScreening(childId);
    return () => {
      stopScreening();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleStartExam = useCallback(() => {
    if (!isAligned || volume > 30) {
      setIsAlertModalOpen(true);
      return;
    }
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
        sidebarContent={
          content ? (
            <ScreeningGuide
              onStart={handleStartExam}
              isReady={isAligned && volume <= 30 && status === 'ready'}
              isAligned={isAligned}
              volume={volume}
              missionData={content}
            />
          ) : (
            <div className="p-8 text-center text-gray-400">가이드 데이터를 찾을 수 없습니다.</div>
          )
        }
      >
        {/* AI 가이드 메시지 오버레이 */}
        {status === 'screening' && guideMessage && (
          <div className="absolute bottom-8 left-1/2 transform -translate-x-1/2 bg-black/70 text-white px-6 py-3 rounded-full text-lg font-medium">
            {guideMessage}
          </div>
        )}
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
    </>
  );
};

export default ExamRecordingPage;