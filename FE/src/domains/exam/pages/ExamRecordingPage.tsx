import React, { useEffect, useState, useCallback } from 'react';
import { useNavigate, useParams } from 'react-router-dom'; // useParams 위치 수정 
import ConfirmModal from '@/components/common/ConfirmModal';
import ExamBaseLayout from '../components/layout/ExamBaseLayout';
import ScreeningGuide from '../components/Screening/ScreeningGuide';
import { useWebRTCScreening } from '../hooks/useWebRTCScreening';

const ExamRecordingPage: React.FC = () => {
  const navigate = useNavigate();
  // ✅ 훅은 컴포넌트 시작 직후에 선언해야 합니다 
  const { missionId } = useParams<{ missionId: string }>(); 
  
  const [isAlertModalOpen, setIsAlertModalOpen] = useState(false);
  const [isPassModalOpen, setIsPassModalOpen] = useState(false);

  // 다음 태스크로 이동하는 함수 
  const handleGoToNextTask = useCallback(() => {
    // URL에 missionId가 없을 경우를 대비해 기본값 1을 설정하거나 예외처리를 합니다 
    const id = missionId || '1';
    navigate(`/exam/screening/${missionId}`);
  }, [navigate, missionId]);

  // 1. WebRTC 스크리닝 훅 사용 
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

  // [기능] 검사 시작 버튼 클릭 시 최종 스크리닝 판정 
  const handleStartExam = useCallback(() => {
    if (!isAligned || volume > 30) {
      // 버튼이 활성화된 상태에서 클릭했을 때만 실행되므로, 
      // 만약 미흡하다면 알림 모달을 띄워줍니다 
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
          <ScreeningGuide onStart={handleStartExam} isReady={isAligned && volume <= 30} />
        }
      >
        {/* 필요한 오버레이 UI가 있다면 여기에 추가  */}
      </ExamBaseLayout>

      {/* 🛠️ 준비 미흡 안내 모달  */}
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

      {/* 🛠️ 스크리닝 성공 확인 모달  */}
      <ConfirmModal
        isOpen={isPassModalOpen}
        onClose={() => setIsPassModalOpen(false)}
        onConfirm={handleGoToNextTask} // ✅ 수정된 함수 연결 
        title="테스트 통과!"
        description="위치와 소음도 측정이 완료되었습니다. 이제 검사가 가능합니다."
        confirmText="검사 시작하기" // 목록보다는 시작하기가 자연스러워요 
      />
    </>
  );
};

export default ExamRecordingPage;