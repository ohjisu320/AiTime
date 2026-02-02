import { SectionHeader } from "../layout/WindowsLayout";

export default function SessionListPanel() {
  return (
    <div className="p-2 h-full bg-white border border-[#808080] font-['Gulim'] overflow-y-auto">
      <SectionHeader title="세션별 영상 목록" />

      {/* [수정 1] 토글(세션) 끼리 간격 확대: gap-1 -> gap-4 */}
      <div className="flex flex-col gap-4 mt-2 px-1">
        {/* 현재 세션 (Active) */}
        <details open className="cursor-pointer group">
          <summary className="font-bold text-[12px] select-none text-black group-hover:text-blue-900">
            ▣ 2024-03-10 (현재)
          </summary>

          {/* [수정 2] 목록 텍스트 위치 내림 (mt-2) 및 아이템 간격(gap-1.5) 조정 */}
          <div className="pl-4 mt-2 flex flex-col gap-1.5 text-[11px] text-blue-800 underline">
            <span className="cursor-pointer hover:font-bold">
              ▷ Task_01: 발화모방
            </span>
            <span className="cursor-pointer hover:font-bold">
              ▷ Task_02: 행동모방
            </span>
            <span className="cursor-pointer hover:font-bold">
              ▷ Task_03: 비대면 호명반응
            </span>
            <span className="cursor-pointer hover:font-bold">
              ▷ Task_04: 대면 호명반응
            </span>
          </div>
        </details>

        {/* 과거 세션 (Mock Data) */}
        {[
          "2024-01-25 (5차)",
          "2023-11-12 (4차)",
          "2023-09-05 (3차)",
          "2023-07-20 (2차)",
        ].map((date, idx) => (
          <details key={idx} className="cursor-pointer text-gray-600 group">
            <summary className="font-bold text-[12px] select-none group-hover:text-black">
              □ {date}
            </summary>
            {/* 내용이 펼쳐졌을 때도 간격 유지 */}
            <div className="pl-4 mt-2 flex flex-col gap-1.5 text-[11px] text-blue-800 underline opacity-80">
              <span className="cursor-pointer hover:font-bold">
                ▷ Task_01: 발화모방
              </span>
              <span className="cursor-pointer hover:font-bold">
                ▷ Task_02: 행동모방
              </span>
              <span className="cursor-pointer hover:font-bold">
                ▷ Task_03: 비대면 호명반응
              </span>
              <span className="cursor-pointer hover:font-bold">
                ▷ Task_04: 대면 호명반응
              </span>
            </div>
          </details>
        ))}
      </div>
    </div>
  );
}
