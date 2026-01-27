// src/domains/exam/pages/ExamPage.tsx
import React, { useEffect, useRef, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useMediaRecorder } from '@/domains/video/hooks/useMediaRecorder';
import { useExamUpload } from '@/domains/video/hooks/useExamUpload'; 
import ExamBaseLayout from '../components/layout/ExamBaseLayout';
import ScreeningGuide from '../components/Screening/ScreeningGuide';
import LoadingSpinner from '@/components/common/LoadingSpinner';
// ✅ 여기가 수정되었습니다!
import { FullScreenOverlayText } from '@/components/common/FullScreenOverlayText'; 
import { SCREENING_CONTENT } from '../constants/missionData';
import Swal from 'sweetalert2';

const ExamPage: React.FC = () => {
  const { missionId = "1" } = useParams<{ missionId: string }>();
  const navigate = useNavigate();
  const videoRef = useRef<HTMLVideoElement>(null);
  
  const content = SCREENING_CONTENT[missionId] || SCREENING_CONTENT["1"];
  const { stream, isRecording, attempts, startSession, startRecording, stopRecording } = useMediaRecorder();
  
  const { mutate: uploadVideo, isPending } = useExamUpload();

  // ⏰ 카운트다운 상태 관리 (5초)
  const [countdown, setCountdown] = useState<number | null>(null);

  useEffect(() => {
    startSession().catch(() => {
      Swal.fire({ title: '권한 에러', text: '카메라 권한을 확인해주세요.', icon: 'warning' })
        .then(() => navigate('/exam/mission'));
    });
  }, [startSession, navigate]);

  useEffect(() => {
    if (videoRef.current && stream) {
      videoRef.current.srcObject = stream;
    }
  }, [stream]);

  // ⚡ 자동 시작 로직: 스트림 연결 -> 카운트다운 시작
  useEffect(() => {
    if (stream && !isRecording && !isPending && countdown === null) {
      setCountdown(5);
    }
  }, [stream, isRecording, isPending, countdown]);

  // ⏰ 카운트다운 타이머 로직
  useEffect(() => {
    if (countdown === null) return;

    if (countdown > 0) {
      const timer = setTimeout(() => {
        setCountdown((prev) => (prev !== null ? prev - 1 : null));
      }, 1000);
      return () => clearTimeout(timer);
    } 
    
    // 0이 되면 녹화 시작
    if (countdown === 0) {
      startRecording();
      setCountdown(null);
    }
  }, [countdown, startRecording]);

  const handleComplete = async () => {
    const videoBlob = await stopRecording();

    // 로컬 다운로드 - 테스트용
    // const localUrl = URL.createObjectURL(videoBlob);
    // const link = document.createElement('a');
    // link.href = localUrl;
    // link.download = `exam_mission_${missionId}_${Date.now()}.mp4`;
    // link.click();
    
    uploadVideo({
      examId: "3fa85f64-5717-4562-b3fc-2c963f66afa6", 
      videoType: `TASK${missionId}`,
      videoBlob,
      attempts
    }, {
      onSuccess: () => {
        // URL.revokeObjectURL(localUrl); 비디오 저장- 테스트용
        navigate('/exam/mission');
      },
      onError: () => {
        Swal.fire('업로드 실패', '전송 중 오류가 발생했습니다. 다시 시도해주세요.', 'error');
      }
    });
  };

  return (
    <ExamBaseLayout
      videoRef={videoRef}
      videoStream={stream}
      isRecording={isRecording}
      isAligned={true}
      volume={0}
      showVisualGuide={false}
      onBack={() => navigate(-1)}
      sidebarContent={
        <div className="h-full relative bg-white">
          {isPending ? (
            <div className="flex flex-col items-center justify-center h-full gap-5 animate-in fade-in duration-500">
              <LoadingSpinner className="w-12 h-12 text-indigo-600" />
              <div className="text-center space-y-2">
                <p className="text-slate-800 text-lg font-bold">영상을 전송하고 있습니다</p>
                <p className="text-slate-400 text-sm">잠시만 기다려 주세요...</p>
              </div>
            </div>
          ) : (
            <ScreeningGuide 
              missionData={content}
              onStart={() => {}} 
              isReady={false}
              isAligned={true}
              volume={0}
              showSystemCheck={false} 
            />
          )}
        </div>
      }
    >
      {/* ⏰ 카운트다운 오버레이 */}
      {countdown !== null && countdown > 0 && (
        <FullScreenOverlayText 
          text={countdown.toString()} 
          subText="준비하세요!" 
        />
      )}

      {/* START! 표시 */}
      {countdown === 0 && (
        <FullScreenOverlayText text="START!" />
      )}

      {/* 녹화 중일 때 하단 종료 버튼 */}
      {isRecording && !isPending && (
        <div className="absolute bottom-12 left-1/2 -translate-x-1/2 z-50">
          <button 
            onClick={handleComplete}
            className="px-14 py-5 bg-rose-600 text-white rounded-full font-black text-xl shadow-[0_10px_40px_rgba(225,29,72,0.4)] hover:scale-105 active:scale-95 transition-all animate-in zoom-in slide-in-from-bottom-5 duration-300"
          >
            미션 완료 및 제출
          </button>
        </div>
      )}
    </ExamBaseLayout>
  );
};

export default ExamPage;