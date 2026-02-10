import { useEffect, useRef } from "react";
import { WindowsButton } from "../layout/WindowsLayout";

interface Props {
  videoUrl: string | null; // [수정] null 허용
  startTime: number;
  onClose: () => void;
}

export default function VideoModal({ videoUrl, startTime, onClose }: Props) {
  const videoRef = useRef<HTMLVideoElement>(null);

  // 모달이 열리면 해당 시간부터 자동 재생
  useEffect(() => {
    if (videoRef.current && videoUrl) {
      videoRef.current.currentTime = startTime;
      videoRef.current.play().catch((e) => console.error("자동 재생 실패:", e));
    }
  }, [videoUrl, startTime]);

  return (
    <div className="fixed inset-0 z-[9999] flex items-center justify-center bg-black/60 backdrop-blur-sm" onClick={onClose}>
      <div
        className="bg-[#d4d0c8] border-2 border-white border-r-[#404040] border-b-[#404040] p-1 shadow-xl flex flex-col gap-1 w-[90%] max-w-[900px]"
        onClick={(e) => e.stopPropagation()} // 내부 클릭 시 닫힘 방지
      >
        {/* 타이틀 바 */}
        <div className="bg-[#000080] text-white px-2 py-1 flex justify-between items-center font-bold font-['Gulim'] text-[13px]">
          <span>비디오 상세 재생</span>
          <WindowsButton onClick={onClose} className="px-2 py-0 text-black">X</WindowsButton>
        </div>

        {/* 비디오 영역 */}
        <div className="bg-black flex items-center justify-center min-h-[500px] border-2 border-[#808080] border-t-[#404040] border-l-[#404040] border-r-white border-b-white relative">
          {videoUrl ? (
            <video
              ref={videoRef}
              src={videoUrl}
              controls
              className="w-full h-full max-h-[80vh] object-contain outline-none"
            />
          ) : (
            <div className="flex flex-col items-center gap-2 text-white font-['Gulim']">
              <div className="text-4xl">🚫</div>
              <div className="text-[14px]">재생할 영상 파일이 없습니다.</div>
              <div className="text-[12px] text-gray-400">(타임라인 데이터만 존재함)</div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}