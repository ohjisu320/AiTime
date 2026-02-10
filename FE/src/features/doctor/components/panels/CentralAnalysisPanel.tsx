import { useState, useRef, useEffect, useCallback } from "react";
import { WindowsContainer, WindowsButton } from "../layout/WindowsLayout";
import { cn } from "@/lib/utils";
import type { VideoAnalysisData } from "../../types/doctor";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";

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
  const [bottomHeight, setBottomHeight] = useState(280);
  const containerRef = useRef<HTMLDivElement>(null);
  const isDraggingBottom = useRef(false);
  const [realDuration, setRealDuration] = useState(0);

  // [Added] Guide Overlay State
  const [showGuide, setShowGuide] = useState(false);

  // 비디오 변경 시 duration 초기화
  useEffect(() => {
    setRealDuration(0);
    // 비디오가 바뀌면 가이드 끄기 (선택사항)
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

  const handleMouseMove = useCallback(
    (e: MouseEvent) => {
      if (!containerRef.current) return;
      const containerRect = containerRef.current.getBoundingClientRect();

      if (isDraggingBottom.current) {
        let newHeight = containerRect.bottom - e.clientY;
        if (newHeight < 200) newHeight = 200;
        if (newHeight > containerRect.height - 150)
          newHeight = containerRect.height - 150;
        setBottomHeight(newHeight);
      }
    },
    [bottomHeight],
  );

  const handleMouseUp = useCallback(() => {
    isDraggingBottom.current = false;
    document.body.style.cursor = "default";
  }, []);

  useEffect(() => {
    window.addEventListener("mousemove", handleMouseMove);
    window.addEventListener("mouseup", handleMouseUp);
    return () => {
      window.removeEventListener("mousemove", handleMouseMove);
      window.removeEventListener("mouseup", handleMouseUp);
    };
  }, [handleMouseMove, handleMouseUp]);

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

  return (
    <div
      ref={containerRef}
      className="grid h-full gap-[2px] min-h-[680px] overflow-hidden"
      style={{
        gridTemplateRows: `1fr 6px ${bottomHeight}px`,
      }}
    >
      <WindowsContainer className="bg-black !border-[#808080] !border-2 flex flex-col p-0 relative min-h-0">
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
                src={analysisData.videoUrl} // null이 아닐 때만 src 할당
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
                      // [Fix] item.time -> step.instruction.startAt
                      const currentStart = step.instruction.startAt;
                      const nextStart = guideSteps[idx + 1] ? guideSteps[idx + 1].instruction.startAt : 9999;

                      const isActive = currentTime >= currentStart && currentTime < nextStart;

                      return (
                        <div key={idx} className={cn("flex gap-2 transition-opacity duration-300", isActive ? "opacity-100 font-bold text-yellow-300" : "opacity-50")}>
                          <span className="font-mono text-[10px] bg-white/10 px-1 rounded h-fit mt-0.5">
                            {currentStart}s
                          </span>
                          <div className="flex flex-col leading-tight">
                            <span>
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

      <div
        className="cursor-row-resize bg-[#d4d0c8] flex items-center justify-center hover:bg-gray-300 border-y border-white active:bg-blue-200 transition-colors z-10"
        onMouseDown={(e) => {
          e.preventDefault();
          isDraggingBottom.current = true;
          document.body.style.cursor = "row-resize";
        }}
      >
        <div className="w-10 h-[4px] bg-gray-400 rounded-full border border-gray-100" />
      </div>

      <div className="flex flex-col gap-[2px] min-h-0 h-full">
        <WindowsContainer className="flex flex-col shrink-0">
          <div className="text-[13px] font-bold bg-[#000080] text-white px-2 py-0.5 flex justify-between items-center shrink-0 mb-1">
            {/* Duration이 0이거나 유효하지 않으면 숨김 */}
            <span>영상 타임라인 분석 {displayDuration > 0 ? `(${displayDuration.toFixed(1)}s)` : ""}</span>
            <span className="bg-black text-[#00ff00] px-2 font-mono text-[14px] border border-white/30 tracking-wider">
              {Math.floor(currentTime)}s
            </span>
          </div>

          <div className="flex flex-col justify-center gap-1.5 bg-[#f0f0f0] border border-gray-400 p-2">
            {(analysisData.rows || []).map((row) => (
              <div key={row.key} className="flex items-center text-[12px] h-6">
                <span className="w-[70px] font-bold shrink-0 text-right pr-2">{row.label}</span>
                <div className="flex-1 h-5 bg-white border border-[#999] relative">
                  {analysisData.timestamps
                    .filter((t) => t.type === row.key)
                    .map((t) => {
                      const durationToUse = displayDuration > 0 ? displayDuration : 1; // 0 나누기 방지
                      const left =
                        (t.startTime / durationToUse) * 100;
                      const width =
                        (t.duration / durationToUse) * 100;
                      return (
                        <Tooltip key={t.id}>
                          <TooltipTrigger asChild>
                            <button
                              onClick={() => handleSeek(t.startTime)}
                              className={cn(
                                "absolute top-0 h-full opacity-80 hover:opacity-100 hover:brightness-110 transition-all border-l border-r border-black/20",
                                row.color,
                              )}
                              style={{
                                left: `${left}%`,
                                width: `${Math.max(width, 2)}%`,
                              }}
                            />
                          </TooltipTrigger>
                          <TooltipContent
                            className="bg-black/90 text-white border-white text-[12px] max-w-[300px]"
                            side="top"
                          >
                            <div className="flex flex-col gap-1">
                              <span className="font-bold text-yellow-300">{t.label}</span>
                              {t.detail && (
                                <span className="text-gray-200 font-normal leading-tight">
                                  {t.detail}
                                </span>
                              )}
                              <span className="text-[10px] text-gray-400">
                                {t.startTime.toFixed(1)}s ~ {(t.startTime + t.duration).toFixed(1)}s
                              </span>
                            </div>
                          </TooltipContent>
                        </Tooltip>
                      );
                    })}
                  <div
                    className="absolute top-0 h-full w-[2px] bg-red-600 z-10 pointer-events-none shadow-[0_0_2px_red]"
                    style={{
                      left: `${(currentTime / (displayDuration > 0 ? displayDuration : 1)) * 100
                        }%`,
                    }}
                  />
                </div>
              </div>
            ))}
            <div className="flex justify-between pl-[70px] text-[11px] text-gray-500 px-1 mt-0.5 select-none">
              <span>0s</span>
              <span>{Math.floor(displayDuration / 2)}s</span>
              <span>{Math.floor(displayDuration)}s</span>
            </div>
          </div>
        </WindowsContainer >

        <WindowsContainer className="flex-1 flex flex-col min-h-0">
          <div className="text-[13px] font-bold mb-1 bg-[#d4d0c8] px-1 py-0.5">
            임상의 종합 소견 메모
          </div>
          <textarea
            className="flex-1 w-full resize-none border border-[#808080] p-2 text-[13px] outline-none font-['Gulim'] leading-relaxed"
            placeholder="환자의 행동 특성 및 진단 소견을 입력하세요..."
          />
        </WindowsContainer>
      </div >
    </div >
  );
}