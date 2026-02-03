import { useState, useRef } from "react";
import {
  WindowsContainer,
  SectionHeader,
  WindowsButton,
} from "../layout/WindowsLayout";
import { cn } from "@/lib/utils";
import type { VideoAnalysisData } from "../../types/doctor";

interface Props {
  onExpandVideo: () => void;
}

const MOCK_ANALYSIS: VideoAnalysisData = {
  videoUrl:
    "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4",
  totalDuration: 60,
  timestamps: [
    { id: 1, type: "parent", label: "부모 지시", startTime: 5, duration: 3 },
    { id: 2, type: "child-vocal", label: "옹알이", startTime: 12, duration: 4 },
    {
      id: 3,
      type: "child-behavior",
      label: "손 흔들기",
      startTime: 25,
      duration: 5,
    },
    { id: 4, type: "child-vocal", label: "울음", startTime: 40, duration: 2 },
    { id: 5, type: "parent", label: "반응 유도", startTime: 50, duration: 5 },
  ],
};

const TIMELINE_ROWS = [
  { key: "parent", label: "부모 행동", color: "bg-gray-500" },
  { key: "child-vocal", label: "아이 음성", color: "bg-green-600" },
  { key: "child-behavior", label: "아이 행동", color: "bg-blue-600" },
] as const;

export default function CentralAnalysisPanel({ onExpandVideo }: Props) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const [currentTime, setCurrentTime] = useState(0);

  const handleSeek = (time: number) => {
    if (videoRef.current) {
      videoRef.current.currentTime = time;
      videoRef.current.play();
    }
  };

  return (
    <div className="grid grid-rows-[160px_1fr_160px] h-full gap-[2px] min-h-[680px] overflow-auto custom-scrollbar">
      {/* 1. 핵심 증상 체크리스트 (스크롤 적용됨) */}
      <WindowsContainer className="flex flex-col min-h-0">
        <SectionHeader title="핵심 증상 체크리스트" />

        {/* 그리드 컨테이너: overflow-hidden으로 고정 */}
        <div className="grid grid-cols-3 gap-1 flex-1 overflow-hidden p-1">
          {["사회성/의사소통", "언어/반복행동", "감각/기타"].map((title, i) => (
            <div
              key={i}
              className="border border-[#808080] p-1 bg-white h-full flex flex-col min-h-0"
            >
              {/* 헤더 (고정) */}
              <span className="font-bold text-[#000080] block border-b border-[#eee] mb-1 pb-1 text-[11px] shrink-0">
                {title}
              </span>

              {/* 내용 목록 (스크롤 가능) */}
              <div className="flex flex-col gap-1 text-[11px] flex-1 overflow-y-auto custom-scrollbar pr-1">
                <label className="flex items-center gap-1 cursor-pointer hover:bg-gray-100">
                  <input type="checkbox" defaultChecked />{" "}
                  <span>호명 반응 부재</span>
                </label>
                <label className="flex items-center gap-1 cursor-pointer hover:bg-gray-100">
                  <input type="checkbox" defaultChecked />{" "}
                  <span>눈맞춤 회피</span>
                </label>
                <label className="flex items-center gap-1 cursor-pointer hover:bg-gray-100">
                  <input type="checkbox" /> <span>표정 부족</span>
                </label>
                <label className="flex items-center gap-1 cursor-pointer hover:bg-gray-100">
                  <input type="checkbox" /> <span>상동 행동</span>
                </label>
                <label className="flex items-center gap-1 cursor-pointer hover:bg-gray-100">
                  <input type="checkbox" /> <span>감각 추구</span>
                </label>
                <label className="flex items-center gap-1 cursor-pointer hover:bg-gray-100">
                  <input type="checkbox" /> <span>반향어 사용</span>
                </label>
              </div>
            </div>
          ))}
        </div>
      </WindowsContainer>

      {/* 2. 비디오 플레이어 */}
      <WindowsContainer className="bg-black !border-[#808080] !border-2 flex flex-col p-0 relative min-h-0">
        <div className="bg-[#d4d0c8] flex justify-between items-center px-2 py-0.5 border-b border-white shrink-0">
          <span className="font-bold text-[11px]">AI 분석 실시간 피드</span>
          <WindowsButton
            onClick={onExpandVideo}
            className="text-[9px] px-1 py-0 h-4"
          >
            [□] 확대
          </WindowsButton>
        </div>

        <div className="flex-1 bg-black overflow-hidden flex items-center justify-center">
          <video
            ref={videoRef}
            src={MOCK_ANALYSIS.videoUrl}
            className="w-full h-full object-contain"
            controls
            onTimeUpdate={(e) => setCurrentTime(e.currentTarget.currentTime)}
          />
        </div>
      </WindowsContainer>

      {/* 3. 하단 메모 & 타임라인 */}
      <div className="flex gap-[2px] min-h-0">
        <WindowsContainer className="flex-1 flex flex-col h-full">
          <div className="text-[11px] font-bold mb-1">
            임상의 종합 소견 메모
          </div>
          <textarea
            className="flex-1 w-full resize-none border border-[#808080] p-1 text-[11px] outline-none font-['Gulim']"
            placeholder="소견 입력..."
          />
        </WindowsContainer>

        <WindowsContainer className="flex-1 flex flex-col h-full">
          <div className="text-[11px] font-bold mb-1 bg-[#000080] text-white px-1 flex justify-between">
            <span>영상 타임라인 분석 ({MOCK_ANALYSIS.totalDuration}s)</span>
            <span>{Math.floor(currentTime)}s</span>
          </div>

          <div className="flex-1 flex flex-col justify-evenly bg-[#f0f0f0] border-t border-l border-white border-r-gray-500 border-b-gray-500 p-1">
            {TIMELINE_ROWS.map((row) => (
              <div key={row.key} className="flex items-center text-[10px] h-6">
                <span className="w-[60px] font-bold shrink-0">{row.label}</span>
                <div className="flex-1 h-4 bg-white border border-[#999] relative mx-1">
                  {MOCK_ANALYSIS.timestamps
                    .filter((t) => t.type === row.key)
                    .map((t) => {
                      const left =
                        (t.startTime / MOCK_ANALYSIS.totalDuration) * 100;
                      const width =
                        (t.duration / MOCK_ANALYSIS.totalDuration) * 100;
                      return (
                        <button
                          key={t.id}
                          onClick={() => handleSeek(t.startTime)}
                          className={cn(
                            "absolute top-0 h-full opacity-80 hover:opacity-100 hover:brightness-110 transition-all border-l border-r border-black/20",
                            row.color,
                          )}
                          style={{
                            left: `${left}%`,
                            width: `${Math.max(width, 2)}%`,
                          }}
                          title={`${t.label} (${t.startTime}s)`}
                        />
                      );
                    })}
                  <div
                    className="absolute top-0 h-full w-[1px] bg-red-600 z-10 pointer-events-none"
                    style={{
                      left: `${(currentTime / MOCK_ANALYSIS.totalDuration) * 100}%`,
                    }}
                  />
                </div>
              </div>
            ))}
            <div className="flex justify-between pl-[60px] text-[9px] text-gray-500 px-1">
              <span>0s</span>
              <span>{Math.floor(MOCK_ANALYSIS.totalDuration / 2)}s</span>
              <span>{MOCK_ANALYSIS.totalDuration}s</span>
            </div>
          </div>
        </WindowsContainer>
      </div>
    </div>
  );
}
