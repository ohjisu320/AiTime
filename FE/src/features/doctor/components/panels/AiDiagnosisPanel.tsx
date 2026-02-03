import { useMemo } from "react";
import { WindowsContainer, WindowsButton } from "../layout/WindowsLayout";

interface Props {
  onExpandAdos: () => void;
  patientAge: number; // [추가]
}

// [데이터 정의는 모달과 동일하게 관리하거나 import 해야 함 - 여기서는 간소화하여 내부 정의]
// 실제로는 shared data로 관리하는 것이 좋습니다.
const MASTER_ITEMS = [
  // ... 모달과 동일한 전체 리스트 (생략 가능하나 완전한 코드를 위해 간략 포함)
  {
    code: "A-2",
    label: "목소리를 내는 빈도",
    score: 1,
    isAi: false,
    cat: "SA",
    groups: ["G1"],
  },
  {
    code: "A-7",
    label: "가리키기",
    score: 2,
    isAi: false,
    cat: "SA",
    groups: ["G2"],
  },
  {
    code: "A-8",
    label: "제스처",
    score: 0,
    isAi: true,
    cat: "SA",
    groups: ["G1"],
  },
  {
    code: "B-1",
    label: "유별난 눈 맞춤",
    score: 1,
    isAi: true,
    cat: "SA",
    groups: ["G1", "G2"],
  },
  {
    code: "B-4",
    label: "타인을 향한 얼굴 표정",
    score: 0,
    isAi: true,
    cat: "SA",
    groups: ["G1", "G2"],
  },
  {
    code: "B-5",
    label: "상호 작용 시도 (통합)",
    score: 2,
    isAi: false,
    cat: "SA",
    groups: ["G1", "G2"],
  },
  {
    code: "B-6",
    label: "공유된 즐거움",
    score: 1,
    isAi: true,
    cat: "SA",
    groups: ["G1"],
  },
  {
    code: "B-7",
    label: "이름에 대한 반응",
    score: 2,
    isAi: true,
    cat: "SA",
    groups: ["G2"],
  },
  {
    code: "B-8",
    label: "무시하기",
    score: 0,
    isAi: false,
    cat: "SA",
    groups: ["G2"],
  },
  {
    code: "B-9",
    label: "요청하기",
    score: 1,
    isAi: false,
    cat: "SA",
    groups: ["G2"],
  },
  {
    code: "B-12",
    label: "보여주기",
    score: 2,
    isAi: false,
    cat: "SA",
    groups: ["G1"],
  },
  {
    code: "B-13",
    label: "합동 주시 시도",
    score: 1,
    isAi: false,
    cat: "SA",
    groups: ["G1", "G2"],
  },
  {
    code: "B-14",
    label: "합동 주시 반응",
    score: 0,
    isAi: false,
    cat: "SA",
    groups: ["G1"],
  },
  {
    code: "B-15",
    label: "상호 작용 시도 질",
    score: 2,
    isAi: false,
    cat: "SA",
    groups: ["G1", "G2"],
  },
  {
    code: "B-16b",
    label: "상호 작용 시도 양",
    score: 1,
    isAi: false,
    cat: "SA",
    groups: ["G2"],
  },
  {
    code: "B-18",
    label: "전반적인 라포의 질",
    score: 1,
    isAi: true,
    cat: "SA",
    groups: ["G2"],
  },
  {
    code: "A-3",
    label: "음성과 언어의 억양",
    score: 0,
    isAi: true,
    cat: "RRB",
    groups: ["G1"],
  },
  {
    code: "D-1",
    label: "특이한 감각적 흥미",
    score: 2,
    isAi: false,
    cat: "RRB",
    groups: ["G1", "G2"],
  },
  {
    code: "D-2",
    label: "손/손가락 움직임",
    score: 2,
    isAi: false,
    cat: "RRB",
    groups: ["G1", "G2"],
  },
  {
    code: "D-5",
    label: "반복적 흥미/상동행동",
    score: 1,
    isAi: false,
    cat: "RRB",
    groups: ["G1", "G2"],
  },
];

export default function AiDiagnosisPanel({ onExpandAdos, patientAge }: Props) {
  // [로직] 간단하게 21개월 이하면 G1, 아니면 G2 (패널에서는 발화여부 자동 가정)
  const currentGroup = patientAge <= 21 ? "G1" : "G2";

  const displayItems = useMemo(() => {
    return MASTER_ITEMS.filter((item) => item.groups.includes(currentGroup));
  }, [currentGroup]);

  return (
    <div className="flex flex-col h-full gap-[2px] font-['Gulim'] text-[11px]">
      <WindowsContainer className="flex-1 flex flex-col min-h-0">
        <div className="flex justify-between items-center mb-1 shrink-0">
          <span className="font-bold text-black">
            ADOS-2 평가 데이터 (
            {currentGroup === "G1" ? "Pre-Verbal" : "Verbal"})
          </span>
          <WindowsButton onClick={onExpandAdos} className="text-[9px] px-1 h-4">
            [□] 확대
          </WindowsButton>
        </div>
        <div className="flex-1 overflow-y-auto border border-[#808080] bg-white">
          <table className="w-full border-collapse text-[10px]">
            <thead className="sticky top-0 bg-[#e2e2e2] z-10">
              <tr>
                <th className="border border-[#999] p-[5px]">항목</th>
                <th className="border border-[#999] p-[5px] w-[30px]">점수</th>
                <th className="border border-[#999] p-[5px] w-[25px]">V</th>
              </tr>
            </thead>
            <tbody>
              {/* SA */}
              <tr className="bg-[#f9f9f9]">
                <td
                  colSpan={3}
                  className="border border-[#ccc] p-[5px] font-bold text-[#000080]"
                >
                  사회적 정동 (SA)
                </td>
              </tr>
              {displayItems
                .filter((i) => i.cat === "SA")
                .map((item, idx) => (
                  <Row key={idx} item={item} />
                ))}
              {/* RRB */}
              <tr className="bg-[#f9f9f9]">
                <td
                  colSpan={3}
                  className="border border-[#ccc] p-[5px] font-bold text-[#000080]"
                >
                  제한적/반복적 행동 (RRB)
                </td>
              </tr>
              {displayItems
                .filter((i) => i.cat === "RRB")
                .map((item, idx) => (
                  <Row key={idx} item={item} />
                ))}
            </tbody>
          </table>
        </div>
      </WindowsContainer>
      {/* 하단 진단 판정 (기존 코드 유지) */}
      <div className="flex flex-col gap-[2px] shrink-0 h-[400px]">
        <div className="bg-white border border-[#808080] p-[5px] text-center shrink-0">
          <div className="bg-[#d4d0c8] font-bold p-1 mb-[5px] text-black">
            AI 진단 판정
          </div>
          <div className="bg-[#ffcccc] text-[#ff0000] border border-[#ff0000] py-[15px] font-bold text-[20px]">
            ASD High Risk
          </div>
        </div>
        <WindowsContainer className="flex-1 flex flex-col min-h-0">
          <div className="bg-[#d4d0c8] font-bold p-1 mb-[5px] text-black">
            진단 근거 및 상세 설명
          </div>
          <textarea
            readOnly
            className="flex-1 w-full resize-none bg-[#f0f0f0] border border-[#808080] p-[10px] text-[12px] font-['Gulim'] leading-relaxed outline-none"
            value={`[AI 분석 근거]\n환자 월령(${patientAge}개월)에 따른 분석 결과...`}
          />
          <WindowsButton className="mt-[5px] w-full h-[40px] font-bold text-[12px]">
            리포트 생성 및 전송
          </WindowsButton>
        </WindowsContainer>
      </div>
    </div>
  );
}

function Row({ item }: { item: any }) {
  return (
    <tr className="hover:bg-blue-50">
      <td className="border border-[#ccc] p-[5px] pl-2">
        <div className="flex items-center gap-1.5">
          <span className="font-bold text-gray-600 w-[28px] inline-block">
            {item.code}
          </span>
          <span>{item.label}</span>
          {item.isAi && (
            <span className="text-[8px] font-bold bg-[#E6F0FF] text-[#0055FF] px-1 rounded-[3px] border border-[#B3D1FF]">
              AI
            </span>
          )}
        </div>
      </td>
      <td className="border border-[#ccc] p-[5px] text-center font-bold">
        {item.score}
      </td>
      <td className="border border-[#ccc] p-[5px] text-center">
        <input type="checkbox" checked readOnly />
      </td>
    </tr>
  );
}
