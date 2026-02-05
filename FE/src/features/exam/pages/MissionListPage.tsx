import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import MissionCard from '@/domains/exam/components/MissionCard';
import ConsentHeader from '@/domains/exam/components/Consent/ConsentHeader';
import InfoNoticeBox from '@/components/common/InfoNoticeBox';
import BigActionButton from '@/components/common/BigActionButton';
import ConfirmModal from '@/components/common/ConfirmModal';
import { useMissions } from '../hooks/useMissions';
import { startAnalysis } from '../api/examApi';
import Swal from 'sweetalert2';
import MissionReviewModal from '@/domains/exam/components/MissionReviewModal';

const MissionListPage: React.FC = () => {
  const navigate = useNavigate();
  const [missions, setMissions] = useState<VideoTask[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  // ✅ 월령 정보 상태 추가
  const [isUnder18, setIsUnder18] = useState<boolean | null>(null);



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

  // const [recheckModal, setRecheckModal] = useState({ isOpen: false, title: '', type: '' });
  const [recheckModal, setRecheckModal] = useState({ isOpen: false, title: '', type: '', videoId: '' }); // ✅ videoId 추가
  const [submitModalOpen, setSubmitModalOpen] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false); // ✅ 제출 상태 관리

  // 진행도 계산: 모든 미션이 UPLOADED 상태인지 확인 
  const completedCount = missions.filter(t => t.status === 'UPLOADED').length;
  const isAllDone = missions.length > 0 && completedCount === missions.length;

  // 카드 클릭 핸들러 (업로드 상태면 재촬영 모달, 아니면 가이드로 이동) 
  const handleCardClick = (task: any) => {
    // const missionNumber = task.videoType.replace('TASK', ''); // 숫자만 추출하던 로직 제거
    if (task.status === 'UPLOADED') {
      // ✅ task.videoId 저장
      setRecheckModal({ isOpen: true, title: task.title, type: task.videoType, videoId: task.videoId });
    } else {
      // ✅ 여기서도 정확한 URL로 이동 (Suffix가 필요하다면 붙일 수 있지만, 라우팅은 보통 BaseType을 쓰거나 ExamPage에서 다시 처리함)
      // 문제: ExamPage는 URL 파라미터를 그대로 missionId로 씀. ExamPage가 Suffix 처리를 하므로 BaseType만 넘겨도 됨.
      // 단, ExamPage URL이 /exam/task/:missionId 구조라면 BaseType만 넘기면 됨.
      navigate(`/exam/guide/${task.videoType}`);
    }
  };

  // 재촬영 확정 핸들러 
  const handleRecheckConfirm = () => {
    // const missionNumber = recheckModal.type.replace('TASK', '');
    setRecheckModal({ ...recheckModal, isOpen: false });
    // 재촬영 시에도 가이드(또는 스크리닝)부터 시작하도록 설정
    navigate(`/exam/guide/${recheckModal.type}`);
  };

  // 로딩 상태 UI 
  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p className="text-xl font-bold text-gray-400 animate-pulse">검사 진행도를 불러오고 있습니다...</p>
      </div>
    );
  }

  // 에러 상태 UI
  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <p className="text-xl font-bold text-red-500 mb-4">데이터를 불러오는 중 오류가 발생했습니다.</p>
          <p className="text-gray-600">{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="w-full flex flex-col items-center pb-20">
      {/* 🚦 공통 헤더 컴포넌트 사용 */}
      <ConsentHeader
        currentStep={3}
        totalSteps={3}
        onBack={() => navigate('/exam/guide')}
      />

      {/* 헤더 높이만큼 여백 확보 (mt-24) */}
      <main className="w-full max-w-[1240px] mt-24 px-6">
        <div className="text-center mb-16">
          <h2 className="text-4xl font-extrabold text-gray-900 mb-4 tracking-tight">검사 미션 선택</h2>
          <p className="text-xl text-gray-500 font-medium">촬영할 미션을 선택해주세요 (총 {missions.length}개 미션을 완료해야 합니다)</p>
        </div>

        <div className="flex gap-10 items-start">
          <div className="flex flex-col gap-6 flex-1">
            {missions.map((task) => {
              // ✅ 여기 수정: getResolvedContent 사용
              const content = getResolvedContent(task.videoType, isUnder18);
              // MissionCard status mapping: EMPTY/FAIL/PASS -> PENDING, UPLOADED -> UPLOADED
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

      {/* 1. 재촬영/확인 모달 */}
      <MissionReviewModal
        isOpen={recheckModal.isOpen}
        title={recheckModal.title}
        examId={localStorage.getItem('examId')}
        // videoType 제거됨
        videoId={recheckModal.videoId} // ✅ 전달
        onClose={() => setRecheckModal({ ...recheckModal, isOpen: false })}
        onRetake={handleRecheckConfirm}
        onDelete={() => {
          setRecheckModal({ ...recheckModal, isOpen: false });
          // 삭제 후 페이지 새로고침 (리스트 상태 업데이트)
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