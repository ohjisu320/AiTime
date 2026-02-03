import { useEffect, useRef } from "react";
import { WindowsButton } from "../layout/WindowsLayout";

interface Props {
  videoUrl: string;
  startTime: number;
  onClose: () => void;
}

export default function VideoModal({ videoUrl, startTime, onClose }: Props) {
  const videoRef = useRef<HTMLVideoElement>(null);

  // 모달이 열리면 자동으로 시작 시간으로 이동 후 재생
  useEffect(() => {
    if (videoRef.current) {
      videoRef.current.currentTime = startTime;
      videoRef.current.play().catch(() => {
        // 브라우저 정책상 자동재생이 막힐 수 있음 (사용자 인터랙션 필요 가능성)
        console.log("Auto-play blocked");
      });
    }
  }, [startTime]);

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
      onClick={onClose}
    >
      <div
        className="w-[80%] h-[80%] bg-[#d4d0c8] border-2 border-white border-r-[#404040] border-b-[#404040] p-1 flex flex-col shadow-xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="bg-[#000080] text-white px-2 py-1 flex justify-between items-center font-bold mb-1 select-none">
          <span>AI 분석 실시간 피드 - 확대</span>
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
