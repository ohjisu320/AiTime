import { WindowsButton } from "../layout/WindowsLayout";

interface Props {
  onClose: () => void;
}

// [Static Data] AiDiagnosisPanel과 동일한 데이터 사용
const ADOS_DATA = [
  {
    section: "[A] 언어 및 의사소통 (Communication)",
    items: [
      { label: "- 가리키기 (Pointing)", score: 2 },
      { label: "- 언어적 보고 및 정보 제공", score: 1 },
    ],
  },
  {
    section: "[B] 사회적 상호작용 (Social Interaction)",
    items: [
      { label: "- 비언어적 의사소통 수단의 통합", score: 2 },
      { label: "- 눈맞춤 및 사회적 미소", score: 3 },
      { label: "- 공유된 즐거움 및 공동주의(JA)", score: 2 },
    ],
  },
  {
    section: "[C] 제한적이고 반복적인 행동 (RRB)",
    items: [
      { label: "- 손 및 손가락의 상동적 움직임", score: 2 },
      { label: "- 감각 자극에 대한 비정상적 관심", score: 2 },
    ],
  },
];

export default function AdosModal({ onClose }: Props) {
  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
      onClick={onClose}
    >
      <div
        className="w-[60%] h-[80%] bg-[#d4d0c8] border-2 border-white border-r-[#404040] border-b-[#404040] p-1 flex flex-col shadow-xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="bg-[#000080] text-white px-2 py-1 flex justify-between items-center font-bold mb-1 select-none">
          <span>ADOS-2 상세 평가 결과 - 확대 보기</span>
          <WindowsButton onClick={onClose}>X 닫기</WindowsButton>
        </div>

        <div className="flex-1 bg-white border-2 border-[#808080] border-r-white border-b-white p-4 overflow-y-auto font-['Gulim'] text-[12px]">
          <h2 className="text-lg font-bold text-[#000080] border-b-2 border-[#000080] mb-4 pb-2">
            ADOS-2 Detailed Score Sheet
          </h2>

          <table className="w-full border-collapse text-[12px]">
            <thead className="bg-[#e2e2e2] sticky top-0 z-10 shadow-sm">
              <tr>
                <th className="border border-[#999] p-[8px] text-center font-bold">
                  평가 영역 및 세부 항목
                </th>
                <th className="border border-[#999] p-[8px] w-[60px] text-center font-bold">
                  점수
                </th>
                <th className="border border-[#999] p-[8px] w-[40px] text-center font-bold">
                  V
                </th>
              </tr>
            </thead>
            <tbody>
              {ADOS_DATA.map((group, groupIdx) => (
                <>
                  {/* 섹션 헤더 */}
                  <tr key={`header-${groupIdx}`} className="bg-[#f9f9f9]">
                    <td
                      colSpan={3}
                      className="border border-[#ccc] p-[8px] font-bold text-[#000080]"
                    >
                      {group.section}
                    </td>
                  </tr>
                  {/* 세부 항목 */}
                  {group.items.map((item, itemIdx) => (
                    <tr
                      key={`item-${groupIdx}-${itemIdx}`}
                      className="hover:bg-blue-50 transition-colors"
                    >
                      <td className="border border-[#ccc] p-[8px]">
                        {item.label}
                      </td>
                      <td className="border border-[#ccc] p-[8px] text-center font-bold">
                        {item.score}
                      </td>
                      <td className="border border-[#ccc] p-[8px] text-center">
                        <input type="checkbox" checked readOnly />
                      </td>
                    </tr>
                  ))}
                </>
              ))}

              {/* 결과 요약 섹션 */}
              <tr className="bg-[#e0e0ff] font-bold border-t-2 border-[#808080]">
                <td className="border border-[#ccc] p-[8px]">
                  사회적 의사소통 합계 (A+B)
                </td>
                <td className="border border-[#ccc] p-[8px] text-center">10</td>
                <td className="border border-[#ccc]"></td>
              </tr>
              <tr className="bg-[#e0e0ff] font-bold">
                <td className="border border-[#ccc] p-[8px]">
                  전체 총점 (Total Score)
                </td>
                <td className="border border-[#ccc] p-[8px] text-center text-red-600 text-[14px]">
                  14
                </td>
                <td className="border border-[#ccc]"></td>
              </tr>
              <tr className="bg-[#fff0f0]">
                <td className="border border-[#ccc] p-[8px] text-red-600 font-bold">
                  판정 기준 (Cut-off)
                </td>
                <td
                  colSpan={2}
                  className="border border-[#ccc] p-[8px] text-center text-red-500 font-bold text-[11px]"
                >
                  ASD 기준: 9점 이상
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
