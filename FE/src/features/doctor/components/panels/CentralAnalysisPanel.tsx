import { useState, useRef, useEffect, useCallback } from "react";
import { WindowsContainer, WindowsButton } from "../layout/WindowsLayout";
import { cn } from "@/lib/utils";
import type { VideoAnalysisData } from "../../types/doctor";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";

interface Props {
  analysisData: VideoAnalysisData;
  onExpandVideo: (currentTime: number) => void;
}



export default function CentralAnalysisPanel({
  analysisData,
  onExpandVideo,
}: Props) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const [currentTime, setCurrentTime] = useState(0);
  const [bottomHeight, setBottomHeight] = useState(280);
  const containerRef = useRef<HTMLDivElement>(null);
  const isDraggingBottom = useRef(false);

  const [realDuration, setRealDuration] = useState(0);

  // 비디오 변경 시 duration 초기화
  useEffect(() => {
    setRealDuration(0);
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
          <WindowsButton
            onClick={handleExpandClick}
            className="text-[11px] px-2 py-0.5"
          >
            [□] 확대
          </WindowsButton>
        </div>

        <div className="flex-1 bg-black overflow-hidden flex items-center justify-center">
          {analysisData.videoUrl ? (
            <video
              ref={videoRef}
              src={analysisData.videoUrl} // null이 아닐 때만 src 할당
              className="w-full h-full object-contain"
              controls
              onTimeUpdate={(e) => setCurrentTime(e.currentTarget.currentTime)}
              onLoadedMetadata={(e) => setRealDuration(e.currentTarget.duration)}
            />
          ) : (
            <div className="text-white text-[13px]">
              🚫 재생할 영상이 없습니다. (타임라인만 확인 가능)
            </div>
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
          <div className="text-[13px] font-bold bg-[#000080] text-white px-2 py-0.5 flex justify-between shrink-0 mb-1">
            <span>영상 타임라인 분석 ({displayDuration.toFixed(1)}s)</span>
            <span>{Math.floor(currentTime)}s</span>
          </div>

          <div className="flex flex-col justify-center gap-1.5 bg-[#f0f0f0] border border-gray-400 p-2">
            {(analysisData.rows || []).map((row) => (
              <div key={row.key} className="flex items-center text-[12px] h-6">
                <span className="w-[70px] font-bold shrink-0 text-right pr-2">{row.label}</span>
                <div className="flex-1 h-5 bg-white border border-[#999] relative">
                  {analysisData.timestamps
                    .filter((t) => t.type === row.key)
                    .map((t) => {
                      const left =
                        (t.startTime / displayDuration) * 100;
                      const width =
                        (t.duration / displayDuration) * 100;
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
                      left: `${(currentTime / displayDuration) * 100
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
        </WindowsContainer>

        <WindowsContainer className="flex-1 flex flex-col min-h-0">
          <div className="text-[13px] font-bold mb-1 bg-[#d4d0c8] px-1 py-0.5">
            임상의 종합 소견 메모
          </div>
          <textarea
            className="flex-1 w-full resize-none border border-[#808080] p-2 text-[13px] outline-none font-['Gulim'] leading-relaxed"
            placeholder="환자의 행동 특성 및 진단 소견을 입력하세요..."
          />
        </WindowsContainer>
      </div>
    </div>
  );
}