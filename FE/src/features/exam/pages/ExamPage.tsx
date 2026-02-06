import React, { useEffect, useRef, useState, useMemo, useCallback } from 'react';
import { useParams, useNavigate, useBlocker, useLocation } from 'react-router-dom';
import { useMediaRecorder } from '@/domains/video/hooks/useMediaRecorder';
import { useExamUpload } from '@/domains/video/hooks/useExamUpload';
import type { VideoType } from '@/domains/video/api/videoApi';
import { getExamInfo } from '@/domains/exam/api/examApi'; // ✅ Import added
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
  const location = useLocation();
  const videoRef = useRef<HTMLVideoElement>(null);

  // ✅ 월령 정보 상태 추가
  const [isUnder18, setIsUnder18] = useState<boolean | null>(null);
  const [isLoadingInfo, setIsLoadingInfo] = useState(true);

  // ✅ childId 가져오기
  const childId = localStorage.getItem('selectedChildId');

  useEffect(() => {
    const fetchExamInfo = async () => {
      if (!childId) {
        console.warn("⚠️ Child ID not found");
        setIsLoadingInfo(false);
        return;
      }
      try {
        const info = await getExamInfo(childId);
        setIsUnder18(info.under18);
      } catch (error) {
        console.error("Failed to fetch exam info:", error);
      } finally {
        setIsLoadingInfo(false);
      }
    };
    fetchExamInfo();
  }, [childId]);

  // ✅ 현재 미션 ID에 월령 접미사 붙이기 (데이터가 있는 경우에만)
  const resolvedMissionId = useMemo(() => {
    if (isUnder18 === null) return missionId; // 로딩 중이거나 에러 시 기본값

    // POSE_IMITATION, SPEECH_IMITATION만 분기 처리
    if (missionId.startsWith("POSE_IMITATION") || missionId.startsWith("SPEECH_IMITATION")) {
      const suffix = isUnder18 ? "_12M" : "_18M";
      // 이미 접미사가 있는지 확인 (중복 방지)
      if (missionId.endsWith("_12M") || missionId.endsWith("_18M")) return missionId;
      return `${missionId}${suffix}`;
    }
    return missionId;
  }, [missionId, isUnder18]);

  // ✅ 부모 행동 미션인지 판별 (문구 표시용)
  const isParentActionMission = useMemo(() => {
    return resolvedMissionId.startsWith('POSE_IMITATION') ||
      resolvedMissionId.startsWith('SPEECH_IMITATION') ||
      resolvedMissionId === 'NAME_NON_FACING' ||
      resolvedMissionId === 'NAME_FACING';
  }, [resolvedMissionId]);

  const content = SCREENING_CONTENT[resolvedMissionId] || SCREENING_CONTENT[missionId] || SCREENING_CONTENT["POSE_IMITATION_12M"];
  const instructions = content?.instructions || [];

  const { stream, isRecording, startSession, startRecording, stopRecording } = useMediaRecorder();
  const { mutate: uploadVideo, isPending } = useExamUpload();

  // ⏰ 타이머 및 상태 관리
  const [phase, setPhase] = useState<'READY' | 'GLOBAL_COUNTDOWN' | 'RECORDING' | 'COMPLETED'>('READY');
  const [globalCount, setGlobalCount] = useState(content?.countdown || 3);
  const [isSuccessModalOpen, setIsSuccessModalOpen] = useState(false);

  // content가 undefined일 경우 방지
  const TOTAL_DURATION = content?.duration || 25;
  const COUNTDOWN_DURATION = content?.countdown || 3;
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
  const [isBlockerModalOpen, setIsBlockerModalOpen] = useState(false);

  useEffect(() => {
    if (blocker.state === 'blocked') {
      setIsBlockerModalOpen(true);
    } else {
      setIsBlockerModalOpen(false);
    }
  }, [blocker]);

  // ✅ 완료 처리 핸들러 (useCallback으로 메모이제이션)
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
    // 🛑 스크리닝 미통과 시 카메라 실행하지 않음 (개발 모드 제외)
    if (!isDev && !location.state?.verified) return;

    startSession().catch(() => {
      Swal.fire({ title: '권한 에러', text: '카메라 권한을 확인해주세요.', icon: 'warning' })
        .then(() => navigate('/exam/mission'));
    });
  }, [startSession, navigate, location.state?.verified, isDev]);

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

  // 🚫 중복 처리 방지 Ref
  const lastProcessedCycleRef = useRef(-1);

  // 5. 녹화 중 글로벌 타이머 (1초마다 증가)
  useEffect(() => {
    if (phase !== 'RECORDING') return;

    const timer = setTimeout(() => {
      setTotalElapsedTime(prev => prev + 1);
    }, 1000);

    return () => clearTimeout(timer);
  }, [phase, totalElapsedTime]);

  // 6. 글로벌 타이머 기반 사이클 전환 로직
  useEffect(() => {
    if (phase !== 'RECORDING') return;

    const currentIdx = currentCycleIndexRef.current;
    const elapsed = totalElapsedTimeRef.current;
    const isSpecialMission = resolvedMissionId.startsWith('POSE_IMITATION') || resolvedMissionId === 'NAME_NON_FACING';

    let cycleEndTime;

    if (isSpecialMission) {
      // 특별 미션: 모든 사이클 동일
      cycleEndTime = (currentIdx + 1) * INSTRUCTION_DURATION;
    } else {
      // 기본 로직: 모든 사이클 동일
      cycleEndTime = (currentIdx + 1) * INSTRUCTION_DURATION;
    }

    console.log(`⏱️ [Timer] Cycle: ${currentIdx}/${instructions.length}, Elapsed: ${elapsed}s, EndTime: ${cycleEndTime}s`);

    // 현재 사이클 종료 시점 도달
    if (elapsed >= cycleEndTime) {
      // 🛡️ 중복 실행 방지
      if (lastProcessedCycleRef.current === currentIdx) {
        console.log(`🛡️ [Guard] Already processed cycle ${currentIdx}. Ignoring.`);
        return;
      }

      lastProcessedCycleRef.current = currentIdx;

      // 마지막 사이클인지 확인
      const isLastCycle = currentIdx >= instructions.length - 1;

      if (isLastCycle) {
        console.log('✅ [Complete] Last cycle finished.');
        handleComplete();
      } else {
        console.log('⏭️ [Next] Moving to next cycle.');
        setCurrentCycleIndex(idx => idx + 1);
      }
    }
  }, [phase, totalElapsedTime, instructions.length, handleComplete, INSTRUCTION_DURATION, resolvedMissionId]);

  // 🎯 현재 상태 계산 (글로벌 타이머 기반)
  const currentInstructionState = useMemo(() => {
    if (phase !== 'RECORDING') return null;
    if (currentCycleIndex >= instructions.length) {
      console.log('⚠️ [State] Invalid Cycle Index:', currentCycleIndex, 'Length:', instructions.length);
      return null;
    }

    const currentInstruction = instructions[currentCycleIndex];
    const isSpecialMission = resolvedMissionId.startsWith('POSE_IMITATION') || resolvedMissionId === 'NAME_NON_FACING';

    // 🎯 특별 미션 로직 (POSE_IMITATION, NAME_NON_FACING)
    if (isSpecialMission) {
      if (currentCycleIndex === 0) {
        // 첫 번째 사이클
        const isShowingNextPreview = totalElapsedTime >= (INSTRUCTION_DURATION - PREP_DURATION) && currentCycleIndex < instructions.length - 1;

        if (totalElapsedTime < PREP_DURATION) {
          // 0~3초: 노란 카드 (WAITING)
          console.log(`🎨 [Special First] WAITING at ${totalElapsedTime}s`);
          return {
            type: 'WAITING',
            instruction: currentInstruction,
            cycleIndex: currentCycleIndex,
            remainingTime: INSTRUCTION_DURATION - totalElapsedTime
          };
        } else if (isShowingNextPreview) {
          // 마지막 3초: 다음 지시사항 노란 카드 미리보기
          const nextInstruction = instructions[currentCycleIndex + 1];
          console.log(`🔮 [Special First Preview] Next instruction at ${totalElapsedTime}s`);
          return {
            type: 'PREVIEW',
            instruction: nextInstruction,
            cycleIndex: currentCycleIndex,
            remainingTime: INSTRUCTION_DURATION - totalElapsedTime
          };
        } else {
          // 3초 ~ (N-3)초: 흰 카드 (INSTRUCTION)
          console.log(`🎨 [Special First] INSTRUCTION at ${totalElapsedTime}s`);
          return {
            type: 'INSTRUCTION',
            instruction: currentInstruction,
            cycleIndex: currentCycleIndex,
            remainingTime: INSTRUCTION_DURATION - totalElapsedTime
          };
        }
      } else {
        // 두 번째 사이클부터: 전체 시간 동안 흰 카드, 마지막 3초만 다음 지시사항 미리보기
        const cycleStartTime = INSTRUCTION_DURATION + (currentCycleIndex - 1) * INSTRUCTION_DURATION;
        const cycleElapsed = totalElapsedTime - cycleStartTime;
        const isShowingNextPreview = cycleElapsed >= (INSTRUCTION_DURATION - PREP_DURATION) && currentCycleIndex < instructions.length - 1;

        if (isShowingNextPreview) {
          // 마지막 3초: 다음 지시사항 노란 카드 미리보기
          const nextInstruction = instructions[currentCycleIndex + 1];
          console.log(`🔮 [Special Preview] Next instruction at ${totalElapsedTime}s`);
          return {
            type: 'PREVIEW',
            instruction: nextInstruction,
            cycleIndex: currentCycleIndex,
            remainingTime: INSTRUCTION_DURATION - cycleElapsed
          };
        } else {
          // 흰 카드
          console.log(`🎨 [Special] INSTRUCTION at ${totalElapsedTime}s`);
          return {
            type: 'INSTRUCTION',
            instruction: currentInstruction,
            cycleIndex: currentCycleIndex,
            remainingTime: INSTRUCTION_DURATION - cycleElapsed
          };
        }
      }
    }

    // 🎯 기본 로직 (SPEECH_IMITATION, NAME_FACING)
    const cycleStartTime = currentCycleIndex * INSTRUCTION_DURATION;
    const cycleElapsed = totalElapsedTime - cycleStartTime;

    // 노란 카드 (준비 단계) - 첫 3초
    const isWaitingPhase = cycleElapsed < PREP_DURATION;

    if (isWaitingPhase) {
      console.log(`🎨 [Default] WAITING at ${totalElapsedTime}s`);
      return {
        type: 'WAITING',
        instruction: currentInstruction,
        cycleIndex: currentCycleIndex,
        remainingTime: INSTRUCTION_DURATION - cycleElapsed
      };
    } else {
      // 흰 카드 (실행 단계)
      console.log(`🎨 [Default] INSTRUCTION at ${totalElapsedTime}s`);
      return {
        type: 'INSTRUCTION',
        instruction: currentInstruction,
        cycleIndex: currentCycleIndex,
        remainingTime: INSTRUCTION_DURATION - cycleElapsed
      };
    }
  }, [phase, currentCycleIndex, instructions, totalElapsedTime, PREP_DURATION, INSTRUCTION_DURATION, resolvedMissionId]);

  const handleModalConfirm = () => {
    setIsSuccessModalOpen(false);
    navigate('/exam/mission'); // 미션 목록으로 이동
  };

  if (isLoadingInfo) {
    return <LoadingSpinner />;
  }

  return (
    <ExamBaseLayout
      videoRef={videoRef}
      videoStream={stream}
      isRecording={isRecording}
      isAligned={true}
      volume={0}
      showVisualGuide={false}
      onBack={() => navigate('/exam/mission')}
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
        <div className="fixed inset-0 z-50 flex flex-col items-center justify-center bg-black/60 backdrop-blur-sm animate-in fade-in duration-300">
          <h1 className="text-[120px] font-black text-white drop-shadow-2xl mb-8 animate-bounce leading-none">
            {globalCount}
          </h1>
          <div className="flex flex-row items-stretch justify-center gap-6 w-full max-w-7xl px-4 flex-wrap">
            {(content.description || "검사 시작").split(/\n\n+/).filter((line: string) => line.trim() !== '').map((line: string, idx: number) => (
              <div
                key={idx}
                className="bg-white rounded-3xl p-8 shadow-2xl text-center flex-1 min-w-[300px] flex items-center justify-center animate-in slide-in-from-left-[20%] fade-in duration-1000 fill-mode-backwards"
                style={{ animationDelay: `${idx * 2800}ms` }}
              >
                <p className="text-2xl font-bold text-gray-900 break-keep leading-snug whitespace-pre-line">
                  {line}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}
      {phase === 'GLOBAL_COUNTDOWN' && globalCount === 0 && (
        <FullScreenOverlayText text="START!" />
      )}

      {/* 2. 녹화 중 지시사항 & 카운트다운 */}
      {phase === 'RECORDING' && currentInstructionState && (
        <>
          {/* 지시사항 카드 */}
          <div className="absolute bottom-10 left-1/2 -translate-x-1/2 w-[90%] max-w-2xl z-40 flex flex-col gap-4">
            {/* 🟡 노란 카드: WAITING (준비) 또는 PREVIEW (다음 지시사항 미리보기) */}
            {(currentInstructionState.type === 'WAITING' || currentInstructionState.type === 'PREVIEW') ? (
              <div
                key={`prep-${currentInstructionState.instruction.id}`}
                className="bg-yellow-300/95 backdrop-blur-xl rounded-3xl p-8 shadow-2xl flex flex-col items-center text-center border-4 border-white/50 transition-all duration-300 animate-in slide-in-from-bottom-5 fade-in"
              >
                <div className="mb-4 px-6 py-2 rounded-full text-lg font-black bg-white text-yellow-600 shadow-sm flex items-center gap-2">
                  <span>✋ {currentInstructionState.type === 'PREVIEW' ? '다음 준비하세요' : '보호자가 먼저 행동 하세요'}</span>
                </div>
                <div className="bg-white/40 rounded-2xl p-6 w-full backdrop-blur-sm mb-4">
                  <p className="text-xl font-bold text-yellow-950 leading-snug break-keep opacity-80 mb-2">
                    {currentInstructionState.type === 'PREVIEW' ? '다음 지시사항' : '다음 지시사항을 따라하세요'}
                  </p>
                  <h3 className="text-2xl font-black text-yellow-900 leading-snug break-keep">
                    {currentInstructionState.instruction.text}
                    {currentInstructionState.instruction.boldText && <span className="text-yellow-700 mx-1">{currentInstructionState.instruction.boldText}</span>}
                    {currentInstructionState.instruction.suffix}
                  </h3>
                </div>
              </div>
            ) : (
              /* ⚪ 흰 카드: INSTRUCTION (실행 단계) */
              <div
                key={`action-${currentInstructionState.instruction.id}`}
                className="bg-white/90 backdrop-blur-xl rounded-3xl p-8 shadow-2xl flex flex-col items-center text-center border border-white/50 transition-all duration-300 scale-100"
              >
                {/* 상단 태그 */}
                {(resolvedMissionId.startsWith('POSE_IMITATION') || resolvedMissionId === 'NAME_NON_FACING') ? (
                  /* 특별 미션: "지금 시작하세요!" 태그 - 2번 깜빡이고 텍스트 변경 */
                  <div
                    className="mb-3 px-4 py-1 rounded-full text-sm font-bold bg-brand-purple text-white relative"
                    style={{ minWidth: '150px', height: '28px' }}
                  >
                    <span
                      className="absolute inset-0 flex items-center justify-center"
                      style={{
                        animation: 'blink-2-times 4s ease-in-out forwards'
                      }}
                    >
                      지금 시작하세요!
                    </span>
                    <span
                      className="absolute inset-0 flex items-center justify-center"
                      style={{
                        animation: 'appear-after-blink 4s ease-in-out forwards',
                        opacity: 0
                      }}
                    >
                      지켜봐 주세요
                    </span>
                  </div>
                ) : (
                  /* 일반 미션: 부모 행동 미션이 아닐 때만 태그 표시 */
                  !isParentActionMission && (
                    <div className="mb-3 px-4 py-1 rounded-full text-sm font-bold bg-brand-purple text-white animate-pulse">
                      지금 시작하세요!
                    </div>
                  )
                )}

                <h3 className={`text-2xl font-bold leading-snug break-keep ${(resolvedMissionId.startsWith('POSE_IMITATION') || resolvedMissionId === 'NAME_NON_FACING') ? 'text-brand-purple' : 'text-gray-900'
                  }`}>
                  {isParentActionMission ? (
                    /* 부모 행동 미션: 관찰 메시지만 표시 */
                    <span className={(resolvedMissionId.startsWith('POSE_IMITATION') || resolvedMissionId === 'NAME_NON_FACING') ? '' : 'text-brand-purple'}>
                      아이의 반응을 지켜봐 주세요
                    </span>
                  ) : (
                    /* 기존 미션: 지시사항 표시 */
                    <>
                      {currentInstructionState.instruction.id && <span className="text-brand-purple mr-2">{currentInstructionState.instruction.id}.</span>}
                      {currentInstructionState.instruction.text}
                      {currentInstructionState.instruction.boldText && <span className={`mx-1 ${(resolvedMissionId.startsWith('POSE_IMITATION') || resolvedMissionId === 'NAME_NON_FACING') ? 'font-black' : 'text-brand-purple'}`}>{currentInstructionState.instruction.boldText}</span>}
                      {currentInstructionState.instruction.suffix}
                    </>
                  )}
                </h3>

                {/* 애니메이션 정의 */}
                <style>{`
                  @keyframes blink-2-times {
                    0% { opacity: 1; }
                    25% { opacity: 0; }
                    50% { opacity: 1; }
                    75% { opacity: 0; }
                    100% { opacity: 0; }
                  }
                  @keyframes appear-after-blink {
                    0%, 75% {
                      opacity: 0;
                    }
                    100% {
                      opacity: 1;
                    }
                  }
                `}</style>
              </div>
            )}

            {/* ⏳ 타이머 게이지 */}
            <div className="w-full h-3 bg-gray-300/50 rounded-full overflow-hidden backdrop-blur-sm shadow-inner mt-4">
              <div
                key={`gauge-${currentCycleIndex}`}
                className={`h-full shadow-md ${
                  // 특별 미션: 첫 사이클 WAITING만 노란색, 나머지는 모두 보라색
                  (resolvedMissionId.startsWith('POSE_IMITATION') || resolvedMissionId === 'NAME_NON_FACING')
                    ? (currentCycleIndex === 0 && currentInstructionState.type === 'WAITING' ? 'bg-yellow-500' : 'bg-brand-purple')
                    // 일반 미션: WAITING/PREVIEW는 노란색, INSTRUCTION은 보라색
                    : (currentInstructionState.type === 'WAITING' || currentInstructionState.type === 'PREVIEW' ? 'bg-yellow-500' : 'bg-brand-purple')
                  }`}
                style={{
                  width: '0%',
                  animation: `grow ${INSTRUCTION_DURATION}s linear forwards`
                }}
              />
              <style>{`
                  @keyframes grow {
                    from { width: 0%; }
                    to { width: 100%; }
                  }
                `}</style>
            </div>
          </div>
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
        disableKeyboardOffset={true}
      />

      {/* 4. 뒤로가기/이탈 방지 모달 */}
      {blocker.state === 'blocked' && (
        <ConfirmModal
          isOpen={isBlockerModalOpen}
          onClose={() => blocker.reset()}
          onConfirm={() => blocker.proceed()}
          title="검사를 중단하시겠습니까?"
          description="페이지를 이동하면 진행 상황이 저장되지 않습니다."
          confirmText="중단하고 나가기"
          confirmVariant="rose"
          closeOnConfirm={false}
          hideCloseButton={true}
          disableKeyboardOffset={true}
        />
      )}

      {/* 5. 비정상 접근 차단 모달 */}
      <ConfirmModal
        isOpen={isInvalidAccessModalOpen}
        onClose={handleInvalidAccessConfirm}
        onConfirm={handleInvalidAccessConfirm}
        title="잘못된 접근입니다."
        description="스크리닝 단계를 먼저 완료해주세요."
        confirmText="확인"
        confirmVariant="violet"
        hideCloseButton={true}
        disableKeyboardOffset={true}
      />
    </ExamBaseLayout>
  );
};

export default ExamPage;