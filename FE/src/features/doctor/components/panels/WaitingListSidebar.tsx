import { useState, useEffect } from "react";
import { cn } from "@/lib/utils"; // Tailwind merge 유틸 (프로젝트에 있다고 가정)

// [Static Mock Data] 환자 대기열 데이터
const MOCK_WAITING_LIST = [
  { id: 1, name: "김철수", gender: "남", age: 5 },
  { id: 2, name: "이영희", gender: "여", age: 4 },
  { id: 3, name: "박영수", gender: "남", age: 6 },
  { id: 4, name: "최지우", gender: "여", age: 4 },
  { id: 5, name: "정민호", gender: "남", age: 5 },
  { id: 6, name: "강수진", gender: "여", age: 6 },
];

interface Props {
  isOpen: boolean;
  onClose: () => void;
}

export default function WaitingListSidebar({ isOpen, onClose }: Props) {
  const [currentTime, setCurrentTime] = useState<string>("");

  // 실시간 시계 기능
  useEffect(() => {
    const updateTime = () => {
      const now = new Date();
      const formatted = now
        .toLocaleString("ko-KR", {
          year: "numeric",
          month: "2-digit",
          day: "2-digit",
          hour: "2-digit",
          minute: "2-digit",
          hour12: false,
        })
        .replace(/\./g, "-")
        .replace(" ", " "); // 포맷 맞춤 (2026-01-30 21:45)
      setCurrentTime(formatted);
    };

    updateTime();
    const timer = setInterval(updateTime, 1000 * 60); // 1분마다 갱신
    return () => clearInterval(timer);
  }, []);

  if (!isOpen) return null;

  return (
    <>
      {/* 배경 오버레이 (클릭 시 닫힘) */}
      <div className="fixed inset-0 bg-black/50 z-[1500]" onClick={onClose} />

      {/* 사이드바 본체 */}
      <div
        className={cn(
          "fixed left-0 top-0 w-[240px] h-full z-[2000] flex flex-col font-['Gulim'] text-[11px]",
          "bg-[#d4d0c8] border-r-2 border-white shadow-2xl transition-transform duration-300",
          isOpen ? "translate-x-0" : "-translate-x-full",
        )}
      >
        {/* 1. 타이틀 바 */}
        <div className="bg-[#000080] text-white p-[3px] flex justify-between items-center select-none">
          <span className="font-bold pl-1">의사/대기열 관리</span>
          <button
            onClick={onClose}
            className="bg-[#d4d0c8] text-black px-2 border-2 border-white border-r-[#404040] border-b-[#404040] active:border-t-[#404040] active:border-l-[#404040] text-[10px] cursor-pointer"
          >
            ◀ 닫기
          </button>
        </div>

        <div className="flex-1 flex flex-col p-[10px] overflow-hidden">
          {/* 2. 의사 정보 */}
          <div className="bg-white border-2 border-[#808080] border-r-white border-b-white p-[8px] mb-[10px]">
            <div className="font-bold text-[#000080] mb-[3px]">
              [담당의 정보]
            </div>
            <div>성명: 박지민 전문의</div>
            <div>소속: 내과 제1진료실</div>
          </div>

          {/* 3. 대기열 검색 및 리스트 */}
          <div className="flex-1 flex flex-col min-h-0">
            <div className="font-bold mb-[5px]">▣ 환자 대기열</div>
            <input
              type="text"
              placeholder="성명 검색..."
              className="w-full h-[22px] bg-white border-2 border-[#808080] border-r-white border-b-white px-[3px] mb-[5px] text-[11px] outline-none"
            />

            <div className="flex-1 bg-white border-2 border-[#808080] border-r-white border-b-white overflow-y-auto mb-[10px]">
              {MOCK_WAITING_LIST.map((patient, index) => (
                <div
                  key={patient.id}
                  className="p-[5px] border-b border-[#ececec] cursor-pointer hover:bg-[#000080] hover:text-white select-none truncate"
                >
                  {String(index + 1).padStart(2, "0")}. {patient.name} (
                  {patient.gender}/{patient.age}세)
                </div>
              ))}
            </div>
          </div>

          {/* 4. 하단 시스템 상태 (Footer) */}
          <div className="mt-auto border-t-2 border-white pt-[10px]">
            <div className="bg-black text-[#0f0] p-[5px] font-mono text-[10px] leading-[1.4] border-2 border-[#808080] border-r-white border-b-white mb-[5px]">
              <div>SERVER: CONNECTED</div>
              <div>AI_ENGINE: v2.4 ACTIVE</div>
              <div>TIME: {currentTime}</div>
            </div>
            <button className="w-full h-[30px] bg-[#d4d0c8] border-2 border-white border-r-[#404040] border-b-[#404040] active:border-t-[#404040] active:border-l-[#404040] font-bold cursor-pointer">
              진단 매뉴얼 (F1)
            </button>
          </div>
        </div>
      </div>
    </>
  );
}
