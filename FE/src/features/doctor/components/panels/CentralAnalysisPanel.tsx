import {
  WindowsContainer,
  SectionHeader,
  WindowsButton,
} from "../layout/WindowsLayout";
import { cn } from "@/lib/utils"; // cn 유틸리티 사용 (없으면 일반 템플릿 리터럴로 대체 가능)

interface Props {
  onExpandVideo: () => void;
}

export default function CentralAnalysisPanel({ onExpandVideo }: Props) {
  return (
    <div className="grid grid-rows-[280px_1fr_200px] h-full gap-[2px]">
      {/* 1. 체크리스트 (생략 - 기존 코드 유지) */}
      <WindowsContainer className="flex flex-col min-h-0">
        <SectionHeader title="핵심 증상 체크리스트" />
        <div className="grid grid-cols-3 gap-1 flex-1 overflow-y-auto p-1">
          {/* ...기존 체크리스트 코드 유지... */}
          {["사회성/의사소통", "언어/반복행동", "감각/기타"].map((title, i) => (
            <div
              key={i}
              className="border border-[#808080] p-1 bg-white h-full flex flex-col"
            >
              <span className="font-bold text-[#000080] block border-b border-[#eee] mb-2 pb-1 text-[11px]">
                {title}
              </span>
              <div className="flex flex-col gap-2 text-[11px]">
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
              </div>
            </div>
          ))}
        </div>
      </WindowsContainer>

      {/* 2. 비디오 (생략 - 기존 코드 유지) */}
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
        <div className="flex-1 flex items-center justify-center bg-black overflow-hidden">
          <span className="text-[#0f0] font-mono animate-pulse text-xs">
            ● MONITORING ACTIVE...
          </span>
        </div>
      </WindowsContainer>

      {/* 3. 하단 메모 & 타임라인 */}
      <div className="flex gap-[2px] min-h-0">
        <WindowsContainer className="flex-1 flex flex-col h-full">
          <div className="text-[11px] font-bold mb-1">
            임상의 종합 소견 메모
          </div>
          <textarea
            className="flex-1 w-full resize-none border border-[#808080] p-1 text-[11px] outline-none"
            placeholder="소견 입력..."
          />
        </WindowsContainer>

        {/* [수정된 부분] 타임라인 색상 적용 */}
        <WindowsContainer className="flex-1 flex flex-col h-full">
          <div className="text-[11px] font-bold mb-1 bg-[#000080] text-white px-1">
            영상 타임라인 분석 (40s)
          </div>
          <div className="flex-1 flex flex-col justify-evenly">
            {[
              { label: "부모 행동", color: "bg-gray-500" }, // 회색
              { label: "아이 음성", color: "bg-green-600" }, // 파란색
              { label: "아이 행동", color: "bg-blue-600" }, // 빨간색
            ].map((item) => (
              <div key={item.label} className="flex items-center text-[10px]">
                <span className="w-[60px] font-bold">{item.label}</span>
                <div className="flex-1 h-3 bg-[#f0f0f0] border border-[#ccc] relative">
                  {/* 마커 색상 적용 */}
                  <div
                    className={cn(
                      "absolute top-0 h-full opacity-80",
                      item.color,
                    )}
                    style={{ left: "20%", width: "10%" }}
                  />
                  {/* 예시용 두 번째 마커 (필요 시 추가) */}
                  <div
                    className={cn(
                      "absolute top-0 h-full opacity-80",
                      item.color,
                    )}
                    style={{ left: "60%", width: "15%" }}
                  />
                </div>
              </div>
            ))}
            <div className="flex justify-between pl-[60px] text-[9px] text-gray-500">
              <span>0s</span>
              <span>10s</span>
              <span>20s</span>
              <span>30s</span>
              <span>40s</span>
            </div>
          </div>
        </WindowsContainer>
      </div>
    </div>
  );
}
