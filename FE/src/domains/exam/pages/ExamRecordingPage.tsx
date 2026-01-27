import React, { useEffect, useState, useCallback } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import ConfirmModal from '@/components/common/ConfirmModal';
import ExamBaseLayout from '../components/layout/ExamBaseLayout';
import ScreeningGuide from '../components/Screening/ScreeningGuide';
import { useWebRTCScreening } from '../hooks/useWebRTCScreening';
import { SCREENING_CONTENT } from '../constants/missionData';

const ExamRecordingPage: React.FC = () => {
  const navigate = useNavigate();
  const { missionId } = useParams<{ missionId: string }>(); 
  
  const [isAlertModalOpen, setIsAlertModalOpen] = useState(false);
  const [isPassModalOpen, setIsPassModalOpen] = useState(false);

  const currentMissionId = missionId || "1";
  const content = SCREENING_CONTENT[currentMissionId] || SCREENING_CONTENT["1"];

  const handleGoToNextTask = useCallback(() => {
    navigate(`/exam/task/${currentMissionId}`);
  }, [navigate, currentMissionId]);

  // 1. WebRTC 스크리닝 훅에서 필요한 상태들 추출
  const { 
    videoRef, 
    isAligned, 
    volume, 
    startCamera: startWebRTC, 
    stopCamera: stopWebRTC 
  } = useWebRTCScreening();

  useEffect(() => {
    startWebRTC();
    return () => {
      stopWebRTC();
    };
  }, [startWebRTC, stopWebRTC]);

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
        videoStream={null}
        isRecording={false} 
        isAligned={isAligned}
        volume={volume}
        onBack={() => navigate('/exam/mission')}
        sidebarContent={
          content ? (
            <ScreeningGuide 
              onStart={handleStartExam} 
              isReady={isAligned && volume <= 30} 
              // ✅ [수정 포인트] 새로 추가된 Props들을 자식에게 전달합니다.
              isAligned={isAligned}
              volume={volume}
              missionData={content}
            />
          ) : (
            <div className="p-8 text-center text-gray-400">가이드 데이터를 찾을 수 없습니다.</div>
          )
        }
      >
        {/* 필요한 오버레이 UI 추가 가능 */}
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