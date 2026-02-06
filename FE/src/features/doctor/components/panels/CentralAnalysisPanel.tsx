import { useState, useRef, useEffect, useCallback } from "react";
import { WindowsContainer, WindowsButton } from "../layout/WindowsLayout";
import { cn } from "@/lib/utils";
import type { VideoAnalysisData } from "../../types/doctor";

interface Props {
  analysisData: VideoAnalysisData;
  onExpandVideo: (currentTime: number) => void;
}

const TIMELINE_ROWS = [
  { key: "parent", label: "부모 행동", color: "bg-gray-500" },
  { key: "child-vocal", label: "아이 음성", color: "bg-green-600" },
  { key: "child-behavior", label: "아이 행동", color: "bg-blue-600" },
] as const;

export default function CentralAnalysisPanel({
  analysisData,
  onExpandVideo,
}: Props) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const [currentTime, setCurrentTime] = useState(0);

  // [수정] 체크리스트 제거로 인해 topHeight 삭제, bottomHeight만 유지
  const [bottomHeight, setBottomHeight] = useState(160);
  const containerRef = useRef<HTMLDivElement>(null);
  const isDraggingBottom = useRef(false);

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

      // [수정] 상단 드래그 로직 삭제, 하단 드래그만 유지
      if (isDraggingBottom.current) {
        let newHeight = containerRect.bottom - e.clientY;
        if (newHeight < 100) newHeight = 100;
        // 최대 높이 제한 (비디오 영역 최소 확보)
        if (newHeight > containerRect.height - 200)
          newHeight = containerRect.height - 200;
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

  return (
    <div
      ref={containerRef}
      className="grid h-full gap-[2px] min-h-[680px] overflow-hidden"
      style={{
        // [수정] 체크리스트 영역 제거 -> Video(1fr) | Handle | Timeline(bottomHeight)
        gridTemplateRows: `1fr 6px ${bottomHeight}px`,
      }}
    >
      {/* 1. 비디오 플레이어 (이제 가장 위로 올라옴) */}
      <WindowsContainer className="bg-black !border-[#808080] !border-2 flex flex-col p-0 relative min-h-0">
        <div className="bg-[#d4d0c8] flex justify-between items-center px-2 py-0.5 border-b border-white shrink-0">
          <span className="font-bold text-[11px]">AI 분석 실시간 피드</span>
          <WindowsButton
            onClick={handleExpandClick}
            className="text-[9px] px-1 py-0 h-4"
          >
            [□] 확대
          </WindowsButton>
        </div>

        <div className="flex-1 bg-black overflow-hidden flex items-center justify-center">
          <video
            ref={videoRef}
            src={analysisData.videoUrl}
            className="w-full h-full object-contain"
            controls
            onTimeUpdate={(e) => setCurrentTime(e.currentTarget.currentTime)}
          />
        </div>
      </WindowsContainer>

      {/* 리사이즈 핸들 (비디오 <-> 타임라인 사이) */}
      <div
        className="cursor-row-resize bg-[#d4d0c8] flex items-center justify-center hover:bg-gray-300 border-y border-white active:bg-blue-200 transition-colors z-10"
        onMouseDown={(e) => {
          e.preventDefault();
          isDraggingBottom.current = true;
          document.body.style.cursor = "row-resize";
        }}
      >
        <div className="w-8 h-[3px] bg-gray-400 rounded-full border border-gray-100" />
      </div>

      {/* 2. 하단 메모 & 타임라인 */}
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
          <div className="text-[11px] font-bold bg-[#000080] text-white px-1 flex justify-between shrink-0">
            <span>영상 타임라인 분석 ({analysisData.totalDuration}s)</span>
            <span>{Math.floor(currentTime)}s</span>
          </div>

          <div className="flex-1 flex flex-col justify-center gap-1 bg-[#f0f0f0] border-t border-l border-white border-r-gray-500 border-b-gray-500 p-1">
            {TIMELINE_ROWS.map((row) => (
              <div key={row.key} className="flex items-center text-[10px] h-5">
                <span className="w-[60px] font-bold shrink-0">{row.label}</span>
                <div className="flex-1 h-4 bg-white border border-[#999] relative mx-1">
                  {analysisData.timestamps
                    .filter((t) => t.type === row.key)
                    .map((t) => {
                      const left =
                        (t.startTime / analysisData.totalDuration) * 100;
                      const width =
                        (t.duration / analysisData.totalDuration) * 100;
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
                      left: `${
                        (currentTime / analysisData.totalDuration) * 100
                      }%`,
                    }}
                  />
                </div>
              </div>
            ))}
            <div className="flex justify-between pl-[60px] text-[9px] text-gray-500 px-1 mt-1">
              <span>0s</span>
              <span>{Math.floor(analysisData.totalDuration / 2)}s</span>
              <span>{analysisData.totalDuration}s</span>
            </div>
          </div>
        </WindowsContainer>
      </div>
    </div>
  );
}
