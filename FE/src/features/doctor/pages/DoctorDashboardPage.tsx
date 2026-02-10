// src/features/doctor/pages/DoctorDashboardPage.tsx
import { useState, useCallback, useMemo } from "react";
import { useDoctorDashboard } from "../hooks/useDoctorDashboard";
import PatientDetailPanel from "../components/panels/PatientDetailPanel";
import SessionListPanel from "../components/panels/SessionListPanel";
import CentralAnalysisPanel from "../components/panels/CentralAnalysisPanel";
import TrendChartPanel from "../components/panels/TrendChartPanel";
import AiDiagnosisPanel from "../components/panels/AiDiagnosisPanel";
import VideoModal from "../components/modals/VideoModal";
import AdosModal from "../components/modals/AdosModal";
import WaitingListSidebar from "../components/panels/WaitingListSidebar";
import DoctorLayout from "../components/layout/DoctorLayout";
import type { VideoAnalysisData, AnalysisTimestamp, TimelineRowConfig } from "../types/doctor";
import type { AdosUpdateRequest, PoseTimestamp, SimpleTimestamp, NonFacingTimestamp } from "@/api/types/examReport.types";

// [추가] 미션 데이터 import (경로가 맞는지 확인해주세요)
import { SCREENING_CONTENT } from "@/domains/exam/constants/missionData";

const DEFAULT_ANALYSIS: VideoAnalysisData = {
  videoUrl: "",
  totalDuration: 0,
  timestamps: [],
  rows: [
    { key: "parent", label: "부모 행동", color: "bg-gray-500" },
    { key: "child-behavior", label: "아이 반응", color: "bg-blue-600" },
  ],
};

export default function DoctorDashboardPage() {
  const { states, actions } = useDoctorDashboard();
  const patientAge = states.selectedPatient?.monthlyAge || 0;

  // [Moved] Determine mission key before analysisData (to use it for props as well)
  const missionKey = useMemo(() => {
    if (!states.currentVideoData) return "";
    const videoData = states.currentVideoData;
    const isUnder18 = patientAge < 18;

    switch (videoData.videoType) {
      case "POSE_IMITATION":
        return isUnder18 ? "POSE_IMITATION_12M" : "POSE_IMITATION_18M";
      case "SPEECH_IMITATION":
        return isUnder18 ? "SPEECH_IMITATION_12M" : "SPEECH_IMITATION_18M";
      case "NAME_NON_FACING":
        return "NAME_NON_FACING";
      case "NAME_FACING":
        return "NAME_FACING";
      default:
        return "";
    }
  }, [states.currentVideoData, patientAge]);

  // [핵심 로직] API 데이터를 UI용 데이터로 변환 (타입별 분기 + 미션 데이터 매핑)
  const analysisData: VideoAnalysisData = useMemo(() => {
    if (!states.currentVideoData) {
      return DEFAULT_ANALYSIS;
    }

    const videoData = states.currentVideoData;
    const uiTimestamps: AnalysisTimestamp[] = [];
    let maxEndTime = 0;

    // 미션 데이터 가져오기 (Uses the key calculated above)
    const missionContent = SCREENING_CONTENT[missionKey];

    // [헬퍼 함수] Trial Index로 구체적인 행동 이름 가져오기
    const getActionLabel = (index: number, type: "parent" | "child", defaultLabel: string) => {
      if (!missionContent || !missionContent.instructions) return defaultLabel;

      // index는 1부터 시작하므로 -1
      const instruction = missionContent.instructions[index - 1];
      if (!instruction) return defaultLabel;

      // 부모 행동일 경우 미션 지침(suffix 등)을 사용하여 구체화
      if (type === "parent") {
        // 예: "정확하게 박수를 쳐주세요" -> "박수 치기" 처럼 간단히 보여주거나 원본 사용
        // 여기서는 suffix나 boldText를 조합해서 보여줌
        return `${instruction.boldText || ""} ${instruction.suffix || ""}`.trim();
      }

      // 아이 행동일 경우
      return `${defaultLabel} (Trial ${index})`;
    };

    // [헬퍼 함수] 툴팁용 상세 설명 가져오기
    const getActionDetail = (index: number) => {
      if (!missionContent || !missionContent.instructions) return undefined;
      const instruction = missionContent.instructions[index - 1];
      if (!instruction) return undefined;

      // 전체 문장 조합 (text + boldText + suffix)
      return `${instruction.text || ""} ${instruction.boldText || ""} ${instruction.suffix || ""}`.trim();
    };


    // [추가] 정적 미션 데이터를 기반으로 '부모 행동' 타임스탬프 생성
    if (missionContent?.instructions) {
      missionContent.instructions.forEach((inst: any, idx: number) => {
        if (inst.startAt !== undefined) {
          uiTimestamps.push({
            id: 10000 + idx, // API 데이터와 충돌 방지
            type: "parent",
            label: getActionLabel(idx + 1, "parent", `부모 행동 ${idx + 1}`),
            detail: getActionDetail(idx + 1),
            startTime: inst.startAt,
            duration: inst.duration || 5, // 기본값
          });
          maxEndTime = Math.max(maxEndTime, inst.startAt + (inst.duration || 5));
        }
      });
    }

    // 비디오 타입에 따른 데이터 매핑 전략 (아이 반응/발화 위주)
    videoData.timestamps?.forEach((ts, idx) => {
      const baseId = (idx + 1) * 10;

      // 1. 동작 모방 (POSE_IMITATION)
      if (videoData.videoType === 'POSE_IMITATION') {
        const item = ts as PoseTimestamp;

        // (A) 기존 포맷 (부모+아이) -> 부모는 위에서 정적으로 추가했으므로 아이만 처리하거나,
        // API에서 부모 데이터가 오더라도 정적 데이터를 우선할지 고민.
        // 요구사항: "부모 행동에 대한 타임스탬프를 안찍고 있어... SCREENING_CONTENT에 내용을 추가해서 담아주면 좋겠어"
        // 즉, API에 없으니 정적으로 찍으라는 뜻.

        if (item.parentStartTime != null && item.childStartTime != null) {
          uiTimestamps.push({
            id: baseId + 2,
            type: "child-behavior",
            label: `모방 시도 (T${item.trialIndex})`,
            startTime: item.childStartTime!,
            duration: item.childEndTime! - item.childStartTime!,
          });
          maxEndTime = Math.max(maxEndTime, item.childEndTime!);
        }
        // [수정] Mock data removal: Removed fallback block using item.startS
      }

      // 2. 발화 모방 (SPEECH_IMITATION)
      else if (videoData.videoType === 'SPEECH_IMITATION') {
        const item = ts as SimpleTimestamp;
        const wordLabel = missionContent?.instructions?.[item.trialIndex - 1]?.text?.replace(/[\[\]]/g, "").trim() || `Trial ${item.trialIndex}`;

        if (item.trialStartS != null) {
          uiTimestamps.push({
            id: baseId,
            type: "child-vocal",
            label: `발화: ${wordLabel}`,
            startTime: item.trialStartS,
            duration: item.trialEndS - item.trialStartS,
          });
          maxEndTime = Math.max(maxEndTime, item.trialEndS);
        }
      }

      // 3. 대면 호명 (NAME_FACING)
      else if (videoData.videoType === 'NAME_FACING') {
        const item = ts as SimpleTimestamp;

        if (item.trialStartS != null) {
          uiTimestamps.push({
            id: baseId,
            type: "child-behavior",
            label: "눈맞춤 확인",
            startTime: item.trialStartS,
            duration: item.trialEndS - item.trialStartS,
          });
          maxEndTime = Math.max(maxEndTime, item.trialEndS);
        }
      }

      // 4. 비대면 호명 (NAME_NON_FACING)
      else if (videoData.videoType === 'NAME_NON_FACING') {
        const item = ts as NonFacingTimestamp;

        // 아이 음성 반응 (voiceStartS/voiceEndS)
        if (item.voiceStartS != null) {
          uiTimestamps.push({
            id: baseId,
            type: "child-vocal",
            label: `음성 반응 (T${item.trialIndex})`,
            startTime: item.voiceStartS,
            duration: item.voiceEndS - item.voiceStartS,
          });
          maxEndTime = Math.max(maxEndTime, item.voiceEndS);
        }
      }
    });

    // [수정] 정적 타임스탬프 주입 로직 제거 (API 데이터만 사용)
    // - 사용자 요청: "들어오는 것만 받게 수정"

    const totalDuration = Math.max(maxEndTime + 5, 60);

    // [동적 타임라인 설정]
    let timelineRows: TimelineRowConfig[] = [];

    // [수정] 데이터 유무와 상관없이 부모/아이 두 줄은 항상 표시하도록 변경
    switch (videoData.videoType) {
      case 'POSE_IMITATION':
        timelineRows = [
          { key: "parent", label: "부모 행동", color: "bg-gray-500" },
          { key: "child-behavior", label: "아이 반응", color: "bg-blue-600" },
        ];
        break;
      case 'SPEECH_IMITATION':
        timelineRows = [
          { key: "parent", label: "부모 행동", color: "bg-gray-500" },
          { key: "child-vocal", label: "아이 반응", color: "bg-green-600" },
        ];
        break;
      case 'NAME_FACING':
        timelineRows = [
          { key: "parent", label: "부모 행동", color: "bg-gray-500" },
          { key: "child-behavior", label: "아이 반응", color: "bg-blue-600" },
        ];
        break;
      case 'NAME_NON_FACING':
        timelineRows = [
          { key: "parent", label: "부모 행동", color: "bg-gray-500" },
          { key: "child-vocal", label: "아이 반응", color: "bg-green-600" },
        ];
        break;
      default:
        timelineRows = [
          { key: "parent", label: "부모 행동", color: "bg-gray-500" },
          { key: "child-vocal", label: "아이 반응", color: "bg-green-600" },
          { key: "child-behavior", label: "아이 행동", color: "bg-blue-600" },
        ];
    }

    // startTime이 null/undefined/NaN인 항목 제거 (안전 필터)
    const safeTimestamps = uiTimestamps.filter(t => t.startTime != null && !isNaN(t.startTime));

    return {
      videoUrl: videoData.viewUrl || null,
      totalDuration,
      timestamps: safeTimestamps,
      rows: timelineRows,
    };
  }, [states.currentVideoData, patientAge]); // patientAge 의존성 추가

  const [videoStartTime, setVideoStartTime] = useState(0);

  const handleAdosSave = useCallback(async (examId: string, scores: AdosUpdateRequest) => {
    await actions.updateAdos(examId, scores);
  }, [actions]);

  const latestExamId = states.currentAdosDetail?.examId ||
    (states.examVideoList.length > 0 ? states.examVideoList[0].examId : undefined);

  return (
    <div className="h-screen w-screen bg-[#808080] flex flex-col overflow-hidden font-['Gulim'] text-[13px]">
      <main className="flex-1 overflow-hidden bg-[#808080] p-[2px]">
        <DoctorLayout
          panels={{
            "waiting-list": (
              <WaitingListSidebar
                onSelectPatient={actions.selectPatient}
              />
            ),
            "patient-detail": (
              <PatientDetailPanel
                patient={states.selectedPatient}
              />
            ),
            "session-list": (
              <SessionListPanel
                examVideoList={states.examVideoList}
                onSelectVideo={actions.selectVideo}
                currentVideoExamId={states.currentVideoData?.examId}
              />
            ),
            "central-analysis": (
              <CentralAnalysisPanel
                analysisData={analysisData}
                isLoading={states.isExamReportLoading}
                onExpandVideo={(currentTime) => {
                  setVideoStartTime(currentTime);
                  actions.setVideoModalOpen(true);
                }}
                // [Added] Props transmission for instruction guide
                missionContent={SCREENING_CONTENT[missionKey]}
                missionKey={missionKey}
              />
            ),
            "trend-chart": (
              <TrendChartPanel
                adosGraphs={states.adosGraphs}
              />
            ),
            "ai-diagnosis": (
              <AiDiagnosisPanel
                onExpandAdos={() => actions.setAdosModalOpen(true)}
                patientAge={patientAge}
                adosDetail={states.currentAdosDetail}
              />
            ),
          }}
        />
      </main>

      {states.isVideoModalOpen && (
        <VideoModal
          videoUrl={analysisData.videoUrl}
          startTime={videoStartTime}
          onClose={() => actions.setVideoModalOpen(false)}
        />
      )}

      {states.isAdosModalOpen && (
        <AdosModal
          onClose={() => actions.setAdosModalOpen(false)}
          patientAge={patientAge}
          adosDetail={states.currentAdosDetail}
          examId={latestExamId}
          onSave={handleAdosSave}
        />
      )}
    </div>
  );
}