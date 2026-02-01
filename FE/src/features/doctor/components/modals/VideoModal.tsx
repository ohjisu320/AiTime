import { WindowsButton } from "../layout/WindowsLayout";

export default function VideoModal({ onClose }: { onClose: () => void }) {
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
          <WindowsButton onClick={onClose}>X 닫기</WindowsButton>
        </div>
        <div className="flex-1 bg-black border-2 border-[#808080] border-r-white border-b-white flex items-center justify-center">
          <span className="text-[#0f0] text-xl font-mono animate-pulse">
            ● MONITORING ACTIVE (ENLARGED)
          </span>
        </div>
      </div>
    </div>
  );
}
