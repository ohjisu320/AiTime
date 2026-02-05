import { useEffect, useRef, useState, useCallback, type MouseEvent } from "react";
import { WindowsButton } from "../layout/WindowsLayout";

interface Props {
  videoUrl: string;
  startTime: number;
  onClose: () => void;
}

export default function VideoModal({ videoUrl, startTime, onClose }: Props) {
  const videoRef = useRef<HTMLVideoElement>(null);

  // 드래그 상태
  const [position, setPosition] = useState({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });

  // 모달이 열리면 자동으로 시작 시간으로 이동 후 재생
  useEffect(() => {
    if (videoRef.current) {
      videoRef.current.currentTime = startTime;
      videoRef.current.play().catch(() => {
        console.log("Auto-play blocked");
      });
    }
  }, [startTime]);

  // 드래그 핸들러
  const handleMouseDown = useCallback((e: MouseEvent<HTMLDivElement>) => {
    setIsDragging(true);
    setDragStart({
      x: e.clientX - position.x,
      y: e.clientY - position.y,
    });
  }, [position]);

  const handleMouseMove = useCallback((e: MouseEvent<HTMLDivElement>) => {
    if (!isDragging) return;
    setPosition({
      x: e.clientX - dragStart.x,
      y: e.clientY - dragStart.y,
    });
  }, [isDragging, dragStart]);

  const handleMouseUp = useCallback(() => {
    setIsDragging(false);
  }, []);

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
      onClick={onClose}
      onMouseMove={handleMouseMove}
      onMouseUp={handleMouseUp}
      onMouseLeave={handleMouseUp}
    >
      <div
        className="w-[80%] h-[80%] bg-[#d4d0c8] border-2 border-white border-r-[#404040] border-b-[#404040] p-1 flex flex-col shadow-xl"
        style={{
          transform: `translate(${position.x}px, ${position.y}px)`,
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* 드래그 가능한 타이틀바 */}
        <div
          className="bg-[#000080] text-white px-2 py-1 flex justify-between items-center font-bold mb-1 select-none"
          style={{ cursor: isDragging ? "grabbing" : "grab" }}
          onMouseDown={handleMouseDown}
        >
          <span>AI 분석 실시간 피드 - 확대 (드래그하여 이동)</span>
          <WindowsButton className="text-black" onClick={onClose}>X 닫기</WindowsButton>
        </div>
        <div className="flex-1 bg-black border-2 border-[#808080] border-r-white border-b-white overflow-hidden flex items-center justify-center">
          <video
            ref={videoRef}
            src={videoUrl}
            className="w-full h-full object-contain"
            controls
          />
        </div>
      </div>
    </div>
  );
}
