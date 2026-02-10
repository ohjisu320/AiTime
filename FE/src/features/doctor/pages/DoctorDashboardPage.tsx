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
  totalDuration: 60,
  timestamps: [],
  rows: [
    { key: "parent", label: "부모 행동", color: "bg-gray-500" },
    { key: "child-vocal", label: "아이 음성", color: "bg-green-600" },
    { key: "child-behavior", label: "아이 행동", color: "bg-blue-600" },
  ],
};

export default function DoctorDashboardPage() {
  const { states, actions } = useDoctorDashboard();
  const patientAge = states.selectedPatient?.monthlyAge || 0;

  // [핵심 로직] API 데이터를 UI용 데이터로 변환 (타입별 분기 + 미션 데이터 매핑)
  const analysisData: VideoAnalysisData = useMemo(() => {
    if (!states.currentVideoData) {
      return DEFAULT_ANALYSIS;
    }

    const videoData = states.currentVideoData;
    const uiTimestamps: AnalysisTimestamp[] = [];
    let maxEndTime = 0;

    // 1. 현재 비디오 타입과 환아 월령에 맞는 미션 데이터 키 찾기
    // (12~17개월 vs 18~23개월 구분 로직)
    const isUnder18 = patientAge < 18; // 12-17개월
    let missionKey = "";

    switch (videoData.videoType) {
      case "POSE_IMITATION":
        missionKey = isUnder18 ? "POSE_IMITATION_12M" : "POSE_IMITATION_18M";
        break;
      case "SPEECH_IMITATION":
        missionKey = isUnder18 ? "SPEECH_IMITATION_12M" : "SPEECH_IMITATION_18M";
        break;
      case "NAME_NON_FACING":
        missionKey = "NAME_NON_FACING";
        break;
      case "NAME_FACING":
        missionKey = "NAME_FACING";
        break;
    }

    // 미션 데이터 가져오기
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


    // 비디오 타입에 따른 데이터 매핑 전략
    videoData.timestamps?.forEach((ts, idx) => {
      const baseId = (idx + 1) * 10;

      // 1. 동작 모방 (POSE_IMITATION)
      if (videoData.videoType === 'POSE_IMITATION') {
        const item = ts as PoseTimestamp;

        // (A) 기존 포맷
        if (item.parentStartTime !== undefined && item.childStartTime !== undefined) {
          // (1) 부모 행동 (Parent) - 구체적 행동 명시
          uiTimestamps.push({
            id: baseId + 1,
            type: "parent",
            label: getActionLabel(item.trialIndex, "parent", `시연 ${item.trialIndex}`),
            detail: getActionDetail(item.trialIndex), // [추가] 상세 설명
            startTime: item.parentStartTime,
            duration: item.parentEndTime - item.parentStartTime,
          });

          // (2) 아이 행동 (Child)
          uiTimestamps.push({
            id: baseId + 2,
            type: "child-behavior",
            label: `모방 시도 (T${item.trialIndex})`,
            startTime: item.childStartTime,
            duration: item.childEndTime - item.childStartTime,
          });
          maxEndTime = Math.max(maxEndTime, item.childEndTime);
        }
        // (B) 신규 포맷 (startS only)
        else if (item.startS !== undefined) {
          const start = item.startS;
          const end = item.endS ?? (start + 5);
          uiTimestamps.push({
            id: baseId,
            type: "child-behavior",
            label: getActionLabel(item.trialIndex, "parent", `Trial ${item.trialIndex}`), // 단일 라인이면 부모 행동명 표시
            detail: getActionDetail(item.trialIndex), // [추가]
            startTime: start,
            duration: end - start,
          });
          maxEndTime = Math.max(maxEndTime, end);
        }
      }

      // 2. 발화 모방 (SPEECH_IMITATION)
      else if (videoData.videoType === 'SPEECH_IMITATION') {
        const item = ts as SimpleTimestamp;
        // 발화 단어 가져오기 (예: "엄마", "맘마")
        const wordLabel = missionContent?.instructions?.[item.trialIndex - 1]?.text?.replace(/[\[\]]/g, "").trim() || `Trial ${item.trialIndex}`;

        if (item.trialStartS !== undefined) {
          uiTimestamps.push({
            id: baseId,
            type: "child-vocal",
            label: `발화: ${wordLabel}`,
            startTime: item.trialStartS,
            duration: item.trialEndS - item.trialStartS,
          });
          maxEndTime = Math.max(maxEndTime, item.trialEndS);
        } else if (item.startS !== undefined) {
          const start = item.startS;
          const end = item.endS ?? (start + 3);
          uiTimestamps.push({
            id: baseId,
            type: "child-vocal",
            label: `발화: ${wordLabel}`,
            detail: getActionDetail(item.trialIndex), // [추가]
            startTime: start,
            duration: end - start,
          });
          maxEndTime = Math.max(maxEndTime, end);
        }
      }

      // 3. 대면 호명 (NAME_FACING)
      else if (videoData.videoType === 'NAME_FACING') {
        const item = ts as SimpleTimestamp;
        // 대면 호명은 instructions가 "이름 부르기" 등으로 단순함
        const label = getActionLabel(item.trialIndex, "parent", `호명 ${item.trialIndex}`);

        if (item.trialStartS !== undefined) {
          uiTimestamps.push({
            id: baseId,
            type: "child-behavior",
            label: label,
            startTime: item.trialStartS,
            duration: item.trialEndS - item.trialStartS,
          });
          maxEndTime = Math.max(maxEndTime, item.trialEndS);
        } else if (item.startS !== undefined) {
          const start = item.startS;
          const end = item.endS ?? (start + 3);
          uiTimestamps.push({
            id: baseId,
            type: "child-behavior",
            label: label,
            detail: getActionDetail(item.trialIndex), // [추가]
            startTime: start,
            duration: end - start,
          });
          maxEndTime = Math.max(maxEndTime, end);
        }
      }

      // 4. 비대면 호명 (NAME_NON_FACING)
      else if (videoData.videoType === 'NAME_NON_FACING') {
        const item = ts as NonFacingTimestamp;

        // (A) 기존 포맷
        if (item.triggerStartS !== undefined) {
          // (1) 시각적 자극/트리거 (Parent 라인)
          uiTimestamps.push({
            id: baseId + 1,
            type: "parent",
            label: `자극 제시 (장난감)`,
            detail: "아이가 오른쪽을 바라볼 수 있게 우측 방향에 장난감이나 주의를 끄는 물건을 배치해 주세요.", // 비대면 자극은 고정 문구
            startTime: item.triggerStartS,
            duration: item.triggerEndS - item.triggerStartS,
          });

          // (2) 호명 (Voice)
          // 호명 멘트 가져오기 (예: "평소 목소리로", "크고 높은 톤으로")
          const voiceLabel = getActionLabel(item.trialIndex, "parent", `호명 ${item.trialIndex}`);

          uiTimestamps.push({
            id: baseId + 2,
            type: "child-vocal", // 타임라인 색상 구분을 위해 vocal 라인 사용
            label: voiceLabel,
            detail: getActionDetail(item.trialIndex), // [추가]
            startTime: item.voiceStartS,
            duration: item.voiceEndS - item.voiceStartS,
          });
          maxEndTime = Math.max(maxEndTime, item.voiceEndS);
        }
        // (B) 신규 포맷
        else if (item.startS !== undefined) {
          const start = item.startS;
          const end = item.endS ?? (start + 3);
          uiTimestamps.push({
            id: baseId,
            type: "parent",
            label: getActionLabel(item.trialIndex, "parent", `Trial ${item.trialIndex}`),
            detail: getActionDetail(item.trialIndex), // [추가]
            startTime: start,
            duration: end - start,
          });
          maxEndTime = Math.max(maxEndTime, end);
        }
      }
    });

    // [수정] 정적 타임스탬프 주입 로직 제거 (API 데이터만 사용)
    // - 사용자 요청: "들어오는 것만 받게 수정"

    const totalDuration = Math.max(maxEndTime + 5, 60);

    // [동적 타임라인 설정]
    let timelineRows: TimelineRowConfig[] = [];
    const hasParentData = uiTimestamps.some(ts => ts.type === 'parent');

    switch (videoData.videoType) {
      case 'POSE_IMITATION':
        timelineRows = [
          ...(hasParentData ? [{ key: "parent", label: "부모 행동", color: "bg-gray-500" }] : []),
          { key: "child-behavior", label: "아이 반응", color: "bg-blue-600" },
        ];
        break;
      case 'SPEECH_IMITATION':
        timelineRows = [
          ...(hasParentData ? [{ key: "parent", label: "부모 행동", color: "bg-gray-500" }] : []),
          { key: "child-vocal", label: "아이 반응", color: "bg-green-600" },
        ];
        break;
      case 'NAME_FACING':
        timelineRows = [
          ...(hasParentData ? [{ key: "parent", label: "부모 행동", color: "bg-gray-500" }] : []),
          { key: "child-behavior", label: "아이 반응", color: "bg-blue-600" },
        ];
        break;
      case 'NAME_NON_FACING':
        timelineRows = [
          ...(hasParentData ? [{ key: "parent", label: "부모 행동", color: "bg-gray-500" }] : []),
          { key: "child-vocal", label: "아이 반응", color: "bg-green-600" },
        ];
        break;
      default:
        timelineRows = [
          ...(hasParentData ? [{ key: "parent", label: "부모 행동", color: "bg-gray-500" }] : []),
          { key: "child-vocal", label: "아이 반응", color: "bg-green-600" },
          { key: "child-behavior", label: "아이 행동", color: "bg-blue-600" },
        ];
    }

    return {
      videoUrl: videoData.viewUrl || null,
      totalDuration,
      timestamps: uiTimestamps,
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