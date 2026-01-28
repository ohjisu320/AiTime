// ----------------------------------------------------------
// Types
// ----------------------------------------------------------
export type VideoType = "TASK1" | "TASK2" | "TASK3" | "TASK4";
export type VideoStatus = "UPLOADED" | "ANALYZING" | "FAILED" | "EMPTY";

export interface AnalysisResult {
  responseTime?: string;
  eyeContact?: string;
  successRate?: string;
  score?: string;
  comment?: string;
}

export interface TaskVideoItem {
  examDate: string;
  videoId: string;
  status: VideoStatus;
  videoUrl?: string | null;
  analysisResult?: AnalysisResult | null;
}

// ----------------------------------------------------------
// Constants & Mock Data
// ----------------------------------------------------------
export const TASK_TABS: { id: VideoType; label: string }[] = [
  { id: "TASK1", label: "동작모방" },
  { id: "TASK2", label: "발화모방" },
  { id: "TASK3", label: "비대면 호명반응" },
  { id: "TASK4", label: "대면 호명 반응" },
];

export const generateMockVideos = (taskType: VideoType): TaskVideoItem[] => {
  const dates = [
    "2026-01-19",
    "2025-12-15",
    "2025-11-30",
    "2025-11-15",
    "2025-10-30",
    "2025-10-15",
  ];

  return dates.map((date, idx) => ({
    examDate: date,
    videoId: `vid-${taskType}-${idx}`,
    status: idx === 0 && taskType === "TASK2" ? "ANALYZING" : "UPLOADED",
    videoUrl:
      idx === 0 && taskType === "TASK2"
        ? null
        : "https://sample-videos.com/video321/mp4/720/big_buck_bunny_720p_1mb.mp4",
    analysisResult: {
      responseTime: `${3 + idx}초`,
      eyeContact: `${5 - idx}회`,
      successRate: `${80 - idx * 5}%`,
      score: `${5 - idx}점`,
      comment: "또래 평균 대비 반응 속도가 상위 10%로 매우 양호합니다.",
    },
  }));
};
