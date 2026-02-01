import { WindowsContainer, WindowsButton } from "../layout/WindowsLayout";

interface Props {
  onExpandAdos: () => void;
}

// [Static Data] ADOS-2 평가 항목 데이터
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

export default function AiDiagnosisPanel({ onExpandAdos }: Props) {
  return (
    <div className="flex flex-col h-full gap-[2px] font-['Gulim'] text-[11px]">
      {/* 1. ADOS-2 평가 데이터 (상단 영역 - 남은 공간 차지) */}
      <WindowsContainer className="flex-1 flex flex-col min-h-0">
        <div className="flex justify-between items-center mb-1 shrink-0">
          <span className="font-bold text-black">ADOS-2 평가 데이터</span>
          <WindowsButton onClick={onExpandAdos} className="text-[9px] px-1 h-4">
            [□] 확대
          </WindowsButton>
        </div>

        {/* 엑셀 스타일 테이블 */}
        <div className="flex-1 overflow-y-auto border border-[#808080] bg-white">
          <table className="w-full border-collapse text-[10px]">
            <thead className="sticky top-0 bg-[#e2e2e2] z-10">
              <tr>
                <th className="border border-[#999] p-[5px] text-center font-bold">
                  평가 영역 및 세부 항목
                </th>
                <th className="border border-[#999] p-[5px] w-[40px] text-center font-bold">
                  점수
                </th>
                <th className="border border-[#999] p-[5px] w-[25px] text-center font-bold">
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
                      className="border border-[#ccc] p-[5px] font-bold"
                    >
                      {group.section}
                    </td>
                  </tr>
                  {/* 세부 항목 */}
                  {group.items.map((item, itemIdx) => (
                    <tr key={`item-${groupIdx}-${itemIdx}`}>
                      <td className="border border-[#ccc] p-[6px]">
                        {item.label}
                      </td>
                      <td className="border border-[#ccc] p-[6px] text-center">
                        {item.score}
                      </td>
                      <td className="border border-[#ccc] p-[6px] text-center">
                        <input type="checkbox" checked readOnly />
                      </td>
                    </tr>
                  ))}
                </>
              ))}

              {/* 합계 및 결과 요약 */}
              <tr className="bg-[#e0e0ff] font-bold border-t-2 border-[#808080]">
                <td className="border border-[#ccc] p-[6px]">
                  사회적 의사소통 합계 (A+B)
                </td>
                <td className="border border-[#ccc] p-[6px] text-center">10</td>
                <td className="border border-[#ccc]"></td>
              </tr>
              <tr className="bg-[#e0e0ff] font-bold">
                <td className="border border-[#ccc] p-[6px]">
                  전체 총점 (Total Score)
                </td>
                <td className="border border-[#ccc] p-[6px] text-center text-red-600">
                  14
                </td>
                <td className="border border-[#ccc]"></td>
              </tr>
              <tr className="bg-[#fff0f0]">
                <td className="border border-[#ccc] p-[6px]">
                  판정 기준 (Cut-off)
                </td>
                <td
                  colSpan={2}
                  className="border border-[#ccc] p-[6px] text-center text-red-500 text-[9px]"
                >
                  ASD 기준: 9점 이상
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </WindowsContainer>

      {/* 2. AI 진단 판정 (하단 고정 영역) */}
      {/* [수정] 높이를 200px -> 400px로 대폭 늘려 내용이 잘리지 않도록 함 */}
      <div className="flex flex-col gap-[2px] shrink-0 h-[400px]">
        {/* 판정 박스 */}
        <div className="bg-white border border-[#808080] p-[5px] text-center shrink-0">
          <div className="bg-[#d4d0c8] font-bold p-1 mb-[5px] text-black">
            AI 진단 판정
          </div>
          <div className="bg-[#ffcccc] text-[#ff0000] border border-[#ff0000] py-[15px] font-bold text-[20px]">
            ASD High Risk
          </div>
        </div>

        {/* 설명 및 버튼 박스 */}
        <WindowsContainer className="flex-1 flex flex-col min-h-0">
          <div className="bg-[#d4d0c8] font-bold p-1 mb-[5px] text-black">
            진단 근거 및 상세 설명
          </div>
          <textarea
            readOnly
            className="flex-1 w-full resize-none bg-[#f0f0f0] border border-[#808080] p-[10px] text-[12px] font-['Gulim'] leading-relaxed outline-none"
            value={`[AI 분석 근거]\n1. 사회적 미소의 빈도가 대조군 대비 70% 낮음.\n2. 특정 자극(비눗방울)에 대한 공동주의 집중 시간 1.2초 미만.\n3. 반복적인 손 흔들기 동작이 세션 내 4회 감지됨.\n4. 호명 시 고개 돌림 반응 성공률 20% 이하.\n\n----------------------------------\n\n위 지표는 ADOS-2 알고리즘 점수 14점과 결합되어 '고위험군'으로 분류되었습니다.`}
          />
          <WindowsButton className="mt-[5px] w-full h-[40px] font-bold text-[12px]">
            리포트 생성 및 전송
          </WindowsButton>
        </WindowsContainer>
      </div>
    </div>
  );
}
