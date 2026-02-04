// src/domains/exam/pages/ExamPage.tsx
import React, { useEffect, useRef, useState, useMemo, useCallback } from 'react';
import { useParams, useNavigate, useBlocker } from 'react-router-dom';
import { useMediaRecorder } from '@/domains/video/hooks/useMediaRecorder';
import { useExamUpload } from '@/domains/video/hooks/useExamUpload';
import type { VideoType } from '@/domains/video/api/videoApi';
import ExamBaseLayout from '@/domains/exam/components/layout/ExamBaseLayout';
import LoadingSpinner from '@/components/common/LoadingSpinner';
import { FullScreenOverlayText } from '@/components/common/FullScreenOverlayText';
import { SCREENING_CONTENT, CLIENT_TO_SERVER_VIDEO_TYPE_MAP } from '@/domains/exam/constants/missionData';
import Swal from 'sweetalert2';
import ConfirmModal from '@/components/common/ConfirmModal';

// Mission ID를 VideoType으로 변환하는 헬퍼 함수
const getVideoTypeFromMissionId = (missionId: string): VideoType => {
  const videoType = CLIENT_TO_SERVER_VIDEO_TYPE_MAP[missionId];
  return (videoType as VideoType) || 'POSE_IMITATION';
};

const ExamPage: React.FC = () => {
  const { missionId = "1" } = useParams<{ missionId: string }>();
  const navigate = useNavigate();
  const videoRef = useRef<HTMLVideoElement>(null);

  const content = SCREENING_CONTENT[missionId] || SCREENING_CONTENT["1"];
  const instructions = content.instructions || [];

  const { stream, isRecording, startSession, startRecording, stopRecording } = useMediaRecorder();
  const { mutate: uploadVideo, isPending } = useExamUpload();

  // ⏰ 타이머 및 상태 관리
  // phase: 'READY' (권한확인) -> 'GLOBAL_COUNTDOWN' (3초) -> 'RECORDING' (25초) -> 'COMPLETED'
  const [phase, setPhase] = useState<'READY' | 'GLOBAL_COUNTDOWN' | 'RECORDING' | 'COMPLETED'>('READY');
  const [globalCount, setGlobalCount] = useState(3);
  const [elapsedTime, setElapsedTime] = useState(0);
  const [isSuccessModalOpen, setIsSuccessModalOpen] = useState(false);

  const TOTAL_DURATION = content.duration || 25; // 각 미션별 시간 적용 (기본 25초)
  const CYCLE_DURATION = 8; // 3초 카운트 + 5초 지시사항

  // 🚫 뒤로가기/이탈 방지 처리
  const shouldBlock = !!stream && phase !== 'COMPLETED';

  useEffect(() => {
    console.log(`🛡️ [Guard Check] shouldBlock: ${shouldBlock}, stream: ${!!stream}, phase: ${phase}`);

    // 새로고침/창닫기 방지 (브라우저 레벨)
    const handleBeforeUnload = (e: BeforeUnloadEvent) => {
      if (shouldBlock) {
        e.preventDefault();
        e.returnValue = '';
      }
    };
    window.addEventListener('beforeunload', handleBeforeUnload);
    return () => window.removeEventListener('beforeunload', handleBeforeUnload);
  }, [shouldBlock, stream, phase]);

  // React Router 네비게이션 방지
  const blocker = useBlocker(shouldBlock);

  useEffect(() => {
    if (blocker.state === 'blocked') {
      Swal.fire({
        title: '검사를 중단하시겠습니까?',
        text: '페이지를 이동하면 영상이 저장되지 않습니다.',
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#3085d6',
        cancelButtonColor: '#d33',
        confirmButtonText: '중단하고 나가기',
        cancelButtonText: '취소',
      }).then((result) => {
        if (result.isConfirmed) {
          blocker.proceed();
        } else {
          blocker.reset();
        }
      });
    }
  }, [blocker]);

  // ✅ 완료 처리 핸들러 (useCallback으로 메모이제이션하고 useEffect보다 위에 정의)
  const handleComplete = useCallback(async () => {
    setPhase('COMPLETED');
    const { blob: videoBlob } = await stopRecording();

    // examId 가져오기
    const examId = localStorage.getItem('examId');
    console.log('🔍 [ExamPage] handleComplete - examId:', examId);

    if (!examId) {
      Swal.fire({ title: '오류', text: '검사 ID가 없습니다.', icon: 'error' });
      return;
    }

    const videoType = getVideoTypeFromMissionId(missionId);
    console.log('🔍 [ExamPage] Upload Params:', {
      examId,
      missionId,
      videoType,
      blobSize: videoBlob.size,
      blobType: videoBlob.type
    });

    // 업로드 Start
    uploadVideo({
      examId,
      videoType,
      videoBlob
    }, {
      onSuccess: () => {
        setIsSuccessModalOpen(true);
      },
      onError: () => {
        Swal.fire('업로드 실패', '다시 시도해주세요.', 'error').then(() => navigate('/exam/mission'));
      }
    });
  }, [stopRecording, uploadVideo, missionId, navigate]);

  // 1. 카메라 권한 및 스트림 연결
  useEffect(() => {
    startSession().catch(() => {
      Swal.fire({ title: '권한 에러', text: '카메라 권한을 확인해주세요.', icon: 'warning' })
        .then(() => navigate('/exam/mission'));
    });
  }, [startSession, navigate]);

  // 2. 스트림 연결 시 비디오 설정
  useEffect(() => {
    if (videoRef.current && stream) {
      videoRef.current.srcObject = stream;
    }
  }, [stream]);

  // 3. 자동 시작 로직: 스트림 준비되면 카운트다운 시작
  useEffect(() => {
    if (stream && phase === 'READY') {
      setPhase('GLOBAL_COUNTDOWN');
    }
  }, [stream, phase]);

  // 4. 글로벌 카운트다운 (3, 2, 1 -> 녹화 시작)
  useEffect(() => {
    if (phase === 'GLOBAL_COUNTDOWN') {
      if (globalCount > 0) {
        const timer = setTimeout(() => setGlobalCount(c => c - 1), 1000);
        return () => clearTimeout(timer);
      } else {
        // 카운트다운 종료 -> 녹화 시작
        startRecording();
        setPhase('RECORDING');
      }
    }
  }, [phase, globalCount, startRecording]);

  // 5. 녹화 중 타이머 (25초)
  useEffect(() => {
    if (phase === 'RECORDING') {
      if (elapsedTime < TOTAL_DURATION) {
        const timer = setInterval(() => {
          setElapsedTime(prev => prev + 1);
        }, 1000);
        return () => clearInterval(timer);
      } else {
        // 시간 종료 -> 녹화 중지 및 완료 처리
        handleComplete();
      }
    }
  }, [phase, elapsedTime, handleComplete]);

  // 🎯 현재 시간에 따른 지시사항 계산
  const currentInstructionState = useMemo(() => {
    if (phase !== 'RECORDING') return null;

    // 현재 사이클 인덱스 (0, 1, 2...)
    const cycleIndex = Math.floor(elapsedTime / CYCLE_DURATION);
    const timeInCycle = elapsedTime % CYCLE_DURATION;

    // 지시사항이 없으면 (범위 초과) null
    if (cycleIndex >= instructions.length) return null;

    const instruction = instructions[cycleIndex];

    // 사이클 내에서: 0~3초(카운트다운), 3~8초(지시사항)
    if (timeInCycle < 3) {
      return { type: 'COUNTDOWN', count: 3 - timeInCycle, instruction }; // 3, 2, 1
    } else {
      return { type: 'INSTRUCTION', instruction };
    }
  }, [elapsedTime, phase, instructions]);

  const handleModalConfirm = () => {
    setIsSuccessModalOpen(false);
    navigate('/exam/mission'); // 미션 목록으로 이동
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
    >
      {/* ⚠️ 로딩 중 (업로드 중 포함) */}
      {isPending && (
        <div className="absolute inset-0 z-50 bg-black/80 flex flex-col items-center justify-center gap-5">
          <LoadingSpinner className="w-16 h-16 text-white" />
          <p className="text-white text-xl font-bold">결과를 저장하고 있습니다...</p>
        </div>
      )}

      {/* 1. 글로벌 카운트다운 (최초 시작 전) */}
      {phase === 'GLOBAL_COUNTDOWN' && globalCount > 0 && (
        <FullScreenOverlayText text={globalCount.toString()} subText="검사 시작" />
      )}
      {phase === 'GLOBAL_COUNTDOWN' && globalCount === 0 && (
        <FullScreenOverlayText text="START!" />
      )}

      {/* 2. 녹화 중 지시사항 & 카운트다운 */}
      {phase === 'RECORDING' && currentInstructionState && (
        <>
          {/* 지시사항 카드 (8초 주기 동안 계속 표시) */}
          <div className="absolute bottom-10 left-1/2 -translate-x-1/2 w-[90%] max-w-2xl z-40 flex flex-col gap-4">
            <div
              key={currentInstructionState.instruction.text} // 텍스트가 바뀔 때만 애니메이션 다시 실행
              className={`bg-white/90 backdrop-blur-xl rounded-3xl p-8 shadow-2xl flex flex-col items-center text-center border border-white/50 transition-all duration-300 ${currentInstructionState.type === 'COUNTDOWN' ? 'animate-in slide-in-from-bottom-10 fade-in' : 'scale-100'
                }`}
            >
              {/* 배지 (준비 vs 시작) */}
              <div
                key={currentInstructionState.type} // 타입 변경 시 애니메이션 리셋
                className={`mb-3 px-4 py-1 rounded-full text-sm font-bold transition-colors duration-300 ${currentInstructionState.type === 'COUNTDOWN'
                  ? "bg-amber-100 text-amber-700"
                  : "bg-brand-purple text-white animate-pulse"
                  }`}
              >
                {currentInstructionState.type === 'COUNTDOWN' ? "준비하세요" : "지금 따라하세요!"}
              </div>

              <h3 className="text-3xl font-bold text-gray-900 leading-snug break-keep">
                {currentInstructionState.instruction.id && <span className="text-brand-purple mr-2">{currentInstructionState.instruction.id}.</span>}
                {currentInstructionState.instruction.text}
                {currentInstructionState.instruction.boldText && <span className="text-brand-purple mx-1">{currentInstructionState.instruction.boldText}</span>}
                {currentInstructionState.instruction.suffix}
              </h3>
            </div>

            {/* ⏳ 타이머 게이지 */}
            <div className="w-full h-3 bg-gray-300/50 rounded-full overflow-hidden backdrop-blur-sm">
              <div
                key={`gauge-${Math.floor(elapsedTime / 8)}`} // 사이클(8초)마다 리셋
                className={`h-full bg-brand-purple ${currentInstructionState.type === 'INSTRUCTION'
                  ? 'w-full animate-[width_5s_linear_forwards]'
                  : 'w-full'
                  }`}
                style={{
                  width: '100%',
                  // Tailwind v4 Arbitrary values not work? use standard style animation if needed.
                  // But the issue was likely the key resetting every second.
                  // Let's also add a clear animation style fallback
                  animation: currentInstructionState.type === 'INSTRUCTION' ? 'shrink 5s linear forwards' : 'none'
                }}
              />
              <style>{`
                @keyframes shrink {
                  from { width: 100%; }
                  to { width: 0%; }
                }
              `}</style>
            </div>
          </div>

          {/* 카운트다운 숫자 오버레이 (카운트다운 단계에서만, 카드 위에 표시) */}
          {currentInstructionState.type === 'COUNTDOWN' && (
            <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 z-50 text-center pointer-events-none">
              <span className="block text-[120px] font-black text-white/90 drop-shadow-[0_4px_24px_rgba(0,0,0,0.5)] animate-in zoom-in fade-in duration-300">
                {currentInstructionState.count}
              </span>
            </div>
          )}
        </>
      )}

      {/* 3. 완료 모달 (성공 시) */}
      <ConfirmModal
        isOpen={isSuccessModalOpen}
        onClose={handleModalConfirm}
        onConfirm={handleModalConfirm}
        title="검사 완료!"
        description="검사가 성공적으로 저장되었습니다."
        confirmText="목록으로 돌아가기"
      />



    </ExamBaseLayout>
  );
};

export default ExamPage;