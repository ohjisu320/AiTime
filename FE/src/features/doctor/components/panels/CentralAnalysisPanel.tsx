import { useState, useRef, useEffect } from "react";
import { WindowsContainer, WindowsButton } from "../layout/WindowsLayout";
import { cn } from "@/lib/utils";
import type { VideoAnalysisData } from "../../types/doctor";
// ... existing imports
// import { PARENT_INTERACTION_TIMESTAMPS } from "@/domains/exam/constants/missionData";

interface Props {
  analysisData: VideoAnalysisData;
  isLoading?: boolean;
  onExpandVideo: (currentTime: number) => void;
  // [Added] Mission context for the guide
  missionContent?: any;
  missionKey?: string;
}

export default function CentralAnalysisPanel({
  analysisData,
  isLoading,
  onExpandVideo,
  missionContent,
}: Props) {

  const videoRef = useRef<HTMLVideoElement>(null);
  const [currentTime, setCurrentTime] = useState(0);
  // [Removed] Resizing logic state and handlers


  const [realDuration, setRealDuration] = useState(0);

  // [Added] Guide Overlay State
  const [showGuide, setShowGuide] = useState(false);

  // 비디오 변경 시 duration 초기화
  useEffect(() => {
    setRealDuration(0);
    setShowGuide(false);
  }, [analysisData.videoUrl]);

  const handleSeek = (time: number) => {
    if (videoRef.current) {
      videoRef.current.currentTime = time;
      videoRef.current.play();
    }
  };

  const handleExpandClick = () => {
    const time = videoRef.current ? videoRef.current.currentTime : 0;
    onExpandVideo(time);
  };

  // 실제 로드된 길이가 있으면 그것을 우선 사용, 없으면 예상 길이 사용
  const displayDuration = realDuration || analysisData.totalDuration;

  // [Added] Helper to get timestamps for the current mission
  const getGuideTimestamps = () => {
    if (!missionContent || !missionContent.instructions) return [];

    // Direct mapping from instructions since startAt is now included
    return missionContent.instructions
      .filter((inst: any) => inst.startAt !== undefined)
      .map((inst: any) => ({
        instruction: inst
      }));
  };

  const guideSteps = getGuideTimestamps();

  // [Added] State for hovered timeline item
  const [hoveredTimelineItem, setHoveredTimelineItem] = useState<{
    label: string;
    detail?: string;
    startTime: number;
    duration: number;
  } | null>(null);

  // [Added] State for selected timeline item (persists on click)
  const [selectedTimelineItem, setSelectedTimelineItem] = useState<{
    label: string;
    detail?: string;
    startTime: number;
    duration: number;
  } | null>(null);

  // [Added] Handler for timeline item click
  const handleTimelineItemClick = (t: any) => {
    handleSeek(t.startTime);
    setSelectedTimelineItem({
      label: t.label,
      detail: t.detail,
      startTime: t.startTime,
      duration: t.duration
    });
  };

  // [Modified] Calculate active step based on hover > selected > current time
  // Moved here to access state variables
  const effectiveTime = hoveredTimelineItem?.startTime ?? selectedTimelineItem?.startTime ?? currentTime;
  let activeStep = guideSteps.find((step: any, idx: number) => {
    const startAt = step.instruction.startAt;
    const nextStart = guideSteps[idx + 1] ? guideSteps[idx + 1].instruction.startAt : 9999;
    return effectiveTime >= startAt && effectiveTime < nextStart;
  });

  // [Added] Fallback: If no step matches exactly (e.g. child response is slightly after), find the most recent previous step
  if (!activeStep && guideSteps.length > 0) {
    activeStep = guideSteps.reduce((prev: any, curr: any) => {
      if (curr.instruction.startAt <= effectiveTime) return curr;
      return prev;
    }, null);
  }

  return (
    <div className="flex flex-col h-full gap-[4px] min-h-[680px] overflow-hidden p-[2px]">

      {/* 1. Video Section (Larger) */}
      <WindowsContainer className="flex-[1.5] bg-black !border-[#808080] !border-2 flex flex-col p-0 relative min-h-0">
        <div className="bg-[#d4d0c8] flex justify-between items-center px-2 py-1 border-b border-white shrink-0">
          <span className="font-bold text-[13px]">AI 분석 실시간 피드</span>
          <div className="flex gap-1">
            <WindowsButton
              onClick={() => setShowGuide(!showGuide)}
              className={cn("text-[11px] px-2 py-0.5", showGuide && "bg-blue-200 border-blue-500 font-bold")}
            >
              [?] 가이드
            </WindowsButton>
            <WindowsButton
              onClick={handleExpandClick}
              className="text-[11px] px-2 py-0.5"
            >
              [□] 확대
            </WindowsButton>
          </div>
        </div>

        <div className="flex-1 bg-black overflow-hidden flex items-center justify-center relative">
          {isLoading || !analysisData.videoUrl ? (
            <div className="flex flex-col items-center justify-center gap-2 select-none">
              <div className="text-[#00ff00] text-[20px] font-bold font-mono tracking-[0.2em] animate-pulse">
                LOADING...
              </div>
              <div className="text-[#00ff00]/60 text-[11px] font-mono tracking-widest">
                WAITING FOR VIDEO SIGNAL
              </div>
            </div>
          ) : (
            <>
              <video
                ref={videoRef}
                src={analysisData.videoUrl}
                className="w-full h-full object-contain"
                controls
                onTimeUpdate={(e) => setCurrentTime(e.currentTarget.currentTime)}
                onLoadedMetadata={(e) => setRealDuration(e.currentTarget.duration)}
              />

              {/* [Added] Guide Overlay */}
              {showGuide && (
                <div className="absolute top-2 right-2 w-[240px] bg-black/80 text-white p-3 rounded border border-white/30 backdrop-blur-sm shadow-xl z-20 pointer-events-none">
                  <h4 className="text-[12px] font-bold text-[#00ff00] mb-2 border-b border-white/20 pb-1">
                    부모 양육 가이드 ({missionContent?.korTitle || "미션"})
                  </h4>
                  <div className="flex flex-col gap-2 text-[11px]">
                    {guideSteps.map((step: any, idx: number) => {
                      const currentStart = step.instruction.startAt;
                      const nextStart = guideSteps[idx + 1] ? guideSteps[idx + 1].instruction.startAt : 9999;
                      const isActive = currentTime >= currentStart && currentTime < nextStart;

                      return (
                        <div key={idx} className={cn("flex gap-2 transition-opacity duration-300", isActive ? "opacity-100 font-bold text-yellow-300" : "opacity-50")}>
                          <span className="font-mono text-[10px] bg-white/10 px-1 rounded h-fit mt-0.5">
                            {currentStart}s
                          </span>
                          <div className="flex flex-col leading-tight">
                            {step.instruction.title && (
                              <span className="font-bold text-[#ffff00] mb-0.5">{step.instruction.title}</span>
                            )}
                            <span className="text-gray-300">
                              {step.instruction.text} <span className="text-[#00ffff]">{step.instruction.boldText}</span> {step.instruction.suffix}
                            </span>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      </WindowsContainer>

      {/* 2. Timeline Section */}
      <WindowsContainer className="flex-1 flex flex-col shrink-0 min-h-0">
        <div className="text-[13px] font-bold bg-[#000080] text-white px-2 py-0.5 flex justify-between items-center shrink-0 mb-1">
          <span>영상 타임라인 분석 {displayDuration > 0 ? `(${displayDuration.toFixed(1)}s)` : ""}</span>
          <span className="bg-black text-[#00ff00] px-2 font-mono text-[14px] border border-white/30 tracking-wider">
            {Math.floor(currentTime)}s
          </span>
        </div>

        <div className="flex-1 flex flex-col justify-center gap-1.5 bg-[#f0f0f0] border border-gray-400 p-2 overflow-y-auto">
          {(analysisData.rows || []).map((row) => (
            <div key={row.key} className="flex items-center text-[12px] h-6 shrink-0">
              <span className="w-[70px] font-bold shrink-0 text-right pr-2">{row.label}</span>
              <div className="flex-1 h-5 bg-white border border-[#999] relative">
                {analysisData.timestamps
                  .filter((t) => t.type === row.key)
                  .map((t) => {
                    const durationToUse = displayDuration > 0 ? displayDuration : 1;
                    const left = (t.startTime / durationToUse) * 100;
                    const width = (t.duration / durationToUse) * 100;
                    return (
                      <button
                        key={t.id}
                        // [Modified] Click sets selection & seeks
                        onClick={() => handleTimelineItemClick(t)}
                        // [Added] Hover handlers for Mission Guide
                        onMouseEnter={() => setHoveredTimelineItem({
                          label: t.label,
                          detail: t.detail,
                          startTime: t.startTime,
                          duration: t.duration
                        })}
                        onMouseLeave={() => setHoveredTimelineItem(null)}
                        className={cn(
                          "absolute top-0 h-full opacity-80 hover:opacity-100 hover:brightness-110 transition-all", // Removed border-black/20
                          row.color,
                          // [Added] Highlight if selected (Use shadow/ring instead of border)
                          selectedTimelineItem?.startTime === t.startTime && "brightness-150 z-10 shadow-[0_0_0_2px_white] shadow-white"
                        )}
                        style={{
                          left: `${left}%`,
                          width: `${Math.max(width, 2)}%`,
                        }}
                      />
                    );
                  })}
                <div
                  className="absolute top-0 h-full w-[2px] bg-red-600 z-10 pointer-events-none shadow-[0_0_2px_red]"
                  style={{
                    left: `${(currentTime / (displayDuration > 0 ? displayDuration : 1)) * 100}%`,
                  }}
                />
              </div>
            </div>
          ))}
          <div className="flex justify-between pl-[70px] text-[11px] text-gray-500 px-1 mt-0.5 select-none shrink-0">
            <span>0s</span>
            <span>{Math.floor(displayDuration / 2)}s</span>
            <span>{Math.floor(displayDuration)}s</span>
          </div>
        </div>
      </WindowsContainer>

      {/* 3. Mission Guide Section */}
      <WindowsContainer className="flex-1 flex flex-col shrink-0 min-h-0 overflow-hidden">
        <div className="text-[13px] font-bold bg-[#000080] text-white px-2 py-0.5 mb-1 flex justify-between items-center shrink-0">
          {/* [Reverted] Fixed Header Title based on user request */}
          <span>{missionContent?.korTitle || "검사 가이드"}</span>
          <span className="text-[11px] font-normal text-gray-300">
            {missionContent?.engTitle}
          </span>
        </div>
        <div className="flex-1 overflow-y-auto bg-white border border-[#808080] p-2 text-[13px] leading-relaxed flex items-center justify-center text-center">
          {(() => {
            // Priority: Hovered > Selected > Active > Empty

            const displayItem = hoveredTimelineItem || selectedTimelineItem;

            if (displayItem) {
              return (
                <div className="flex flex-col items-center gap-2 animate-in fade-in zoom-in duration-300">
                  <span className={cn(
                    "font-mono text-[11px] text-white px-2 py-0.5 rounded-full mb-1",
                    hoveredTimelineItem ? "bg-purple-700" : "bg-blue-700" // Different color for selected vs hovered
                  )}>
                    {displayItem.startTime}s ~ {(displayItem.startTime + displayItem.duration).toFixed(0)}s
                  </span>
                  <div className="text-[15px] font-bold text-gray-800 leading-snug break-keep">
                    {displayItem.detail || displayItem.label}
                  </div>
                </div>
              );
            }

            if (guideSteps.length === 0) {
              return <div className="text-gray-400">등록된 가이드 데이터가 없습니다.</div>;
            }

            if (!activeStep) {
              return (
                <div className="flex flex-col items-center gap-2">
                  <span className="text-gray-500 font-bold">검사 준비 중...</span>
                  <span className="text-[11px] text-gray-400">잠시 후 검사가 시작됩니다.</span>
                </div>
              );
            }

            const { instruction } = activeStep;

            return (
              <div className="flex flex-col items-center gap-2 animate-in fade-in zoom-in duration-300">
                <span className="font-mono text-[11px] bg-black text-[#00ff00] px-2 py-0.5 rounded-full mb-1">
                  STEP {instruction.id} ({instruction.startAt}s ~)
                  {instruction.title && ` - ${instruction.title}`}
                </span>
                <div className="text-[15px] font-bold text-gray-800 leading-snug break-keep">
                  {instruction.text}{" "}
                  <span className="text-blue-600 underline decoration-blue-400 underline-offset-4 decoration-2">
                    {instruction.boldText}
                  </span>{" "}
                  {instruction.suffix}
                </div>
              </div>
            );
          })()}
        </div>
      </WindowsContainer>

      {/* 4. Memo Section */}
      <WindowsContainer className="flex-1 flex flex-col shrink-0 min-h-0">
        <div className="text-[13px] font-bold mb-1 bg-[#d4d0c8] px-1 py-0.5 shrink-0">
          임상의 종합 소견 메모
        </div>
        <textarea
          className="flex-1 w-full resize-none border border-[#808080] p-2 text-[13px] outline-none font-['Gulim'] leading-relaxed"
          placeholder="환자의 행동 특성 및 진단 소견을 입력하세요..."
        />
      </WindowsContainer>
    </div>
  );
}