import { useState, useMemo } from "react";
import { WindowsButton } from "../layout/WindowsLayout";
import { cn } from "@/lib/utils";
import type { AdosItemDefinition, AdosAiResult } from "../../types/ados";

interface Props {
  onClose: () => void;
  patientAge: number;
}

// [Master List]
const MASTER_ADOS_ITEMS: AdosItemDefinition[] = [
  // SA: Communication
  {
    code: "A-2",
    label: "목소리를 내는 빈도",
    category: "SA",
    subCategory: "Communication",
    isAiAnalyzed: false,
  },
  {
    code: "A-7",
    label: "가리키기 (Pointing)",
    category: "SA",
    subCategory: "Communication",
    isAiAnalyzed: false,
  },
  {
    code: "A-8",
    label: "제스처",
    category: "SA",
    subCategory: "Communication",
    isAiAnalyzed: true,
    aiSourceTask: "동작모방 과제 분석",
  },
  // SA: Interaction
  {
    code: "B-1",
    label: "유별난 눈 맞춤",
    category: "SA",
    subCategory: "Interaction",
    isAiAnalyzed: true,
    aiSourceTask: "대면호명 과제 분석",
  },
  {
    code: "B-4",
    label: "타인을 향한 얼굴 표정",
    category: "SA",
    subCategory: "Interaction",
    isAiAnalyzed: true,
    aiSourceTask: "대면호명 과제 분석",
  },
  {
    code: "B-5",
    label: "사회적 상호 작용 시도 (통합)",
    category: "SA",
    subCategory: "Interaction",
    isAiAnalyzed: false,
  },
  {
    code: "B-6",
    label: "공유된 즐거움",
    category: "SA",
    subCategory: "Interaction",
    isAiAnalyzed: true,
    aiSourceTask: "대면호명/동작모방 TF 종합",
  },
  {
    code: "B-7",
    label: "이름에 대한 반응",
    category: "SA",
    subCategory: "Interaction",
    isAiAnalyzed: true,
    aiSourceTask: "비대면호명 과제 분석",
  },
  {
    code: "B-8",
    label: "무시하기",
    category: "SA",
    subCategory: "Interaction",
    isAiAnalyzed: false,
  },
  {
    code: "B-9",
    label: "요청하기",
    category: "SA",
    subCategory: "Interaction",
    isAiAnalyzed: false,
  },
  {
    code: "B-12",
    label: "보여주기",
    category: "SA",
    subCategory: "Interaction",
    isAiAnalyzed: false,
  },
  {
    code: "B-13",
    label: "합동 주시 자발적 시도",
    category: "SA",
    subCategory: "Interaction",
    isAiAnalyzed: false,
  },
  {
    code: "B-14",
    label: "합동 주시에 대한 반응",
    category: "SA",
    subCategory: "Interaction",
    isAiAnalyzed: false,
  },
  {
    code: "B-15",
    label: "사회적 상호 작용 시도 질",
    category: "SA",
    subCategory: "Interaction",
    isAiAnalyzed: false,
  },
  {
    code: "B-16b",
    label: "상호 작용 시도 양 (부모)",
    category: "SA",
    subCategory: "Interaction",
    isAiAnalyzed: false,
  },
  {
    code: "B-18",
    label: "전반적인 라포의 질",
    category: "SA",
    subCategory: "Interaction",
    isAiAnalyzed: true,
    aiSourceTask: "전체 과제 TF 종합",
  },
  // RRB
  {
    code: "A-3",
    label: "음성과 언어의 억양",
    category: "RRB",
    subCategory: "RRB_General",
    isAiAnalyzed: true,
    aiSourceTask: "발화모방 과제 분석",
  },
  {
    code: "D-1",
    label: "특이한 감각적 흥미",
    category: "RRB",
    subCategory: "RRB_General",
    isAiAnalyzed: false,
  },
  {
    code: "D-2",
    label: "손과 손가락 움직임/자세",
    category: "RRB",
    subCategory: "RRB_General",
    isAiAnalyzed: false,
  },
  {
    code: "D-5",
    label: "특이한 반복적 흥미/상동행동",
    category: "RRB",
    subCategory: "RRB_General",
    isAiAnalyzed: false,
  },
];

const CODES_PRE_VERBAL = [
  "A-2",
  "A-8",
  "B-1",
  "B-4",
  "B-5",
  "B-6",
  "B-12",
  "B-13",
  "B-14",
  "B-15",
  "A-3",
  "D-1",
  "D-2",
  "D-5",
];
const CODES_VERBAL = [
  "A-7",
  "B-1",
  "B-4",
  "B-5",
  "B-7",
  "B-8",
  "B-9",
  "B-13",
  "B-15",
  "B-16b",
  "B-18",
  "D-1",
  "D-2",
  "D-5",
];

const MOCK_AI_RESULTS: AdosAiResult = {
  "A-8": 0,
  "B-1": 1,
  "B-4": 0,
  "B-6": 1,
  "B-7": 2,
  "B-18": 1,
  "A-3": 0,
};

export default function AdosModal({ onClose, patientAge }: Props) {
  const [doctorScores, setDoctorScores] = useState<Record<string, string>>({});

  const [isVerbal, setIsVerbal] = useState<boolean>(patientAge > 21);

  const currentItems = useMemo(() => {
    if (patientAge >= 12 && patientAge <= 21) {
      return MASTER_ADOS_ITEMS.filter((item) =>
        CODES_PRE_VERBAL.includes(item.code),
      );
    }
    return isVerbal
      ? MASTER_ADOS_ITEMS.filter((item) => CODES_VERBAL.includes(item.code))
      : MASTER_ADOS_ITEMS.filter((item) =>
          CODES_PRE_VERBAL.includes(item.code),
        );
  }, [patientAge, isVerbal]);

  const handleScoreChange = (code: string, value: string) => {
    setDoctorScores((prev) => ({ ...prev, [code]: value }));
  };

  const calculateTotal = (category: "SA" | "RRB") => {
    return currentItems
      .filter((item) => item.category === category)
      .reduce((sum, item) => {
        let score = 0;
        if (typeof MOCK_AI_RESULTS[item.code] === "number") {
          score = MOCK_AI_RESULTS[item.code] as number;
        } else if (
          doctorScores[item.code] !== undefined &&
          doctorScores[item.code] !== ""
        ) {
          score = parseInt(doctorScores[item.code], 10);
        }
        return sum + (isNaN(score) ? 0 : score);
      }, 0);
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
      onClick={onClose}
    >
      <div
        className="w-[900px] h-[90%] bg-[#d4d0c8] border-2 border-white border-r-[#404040] border-b-[#404040] p-1 flex flex-col shadow-xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="bg-[#000080] text-white px-2 py-1 flex justify-between items-center font-bold mb-1 select-none shrink-0">
          <span>ADOS-2 진단 결과 입력표 (Module T)</span>
          <WindowsButton className="text-black" onClick={onClose}>
            X 닫기
          </WindowsButton>
        </div>

        <div className="bg-[#f0f0f0] border border-[#808080] p-2 mb-1 flex items-center gap-4 text-[12px] shrink-0">
          <span className="font-bold">검사 기준:</span>
          <label className="flex items-center gap-1 cursor-pointer">
            <input
              type="checkbox"
              checked={isVerbal}
              onChange={(e) => setIsVerbal(e.target.checked)}
              disabled={patientAge <= 21}
            />
            <span>발화 가능 (21개월 이상)</span>
          </label>
          <span className="ml-auto font-bold text-blue-800">
            [{patientAge}개월 / {isVerbal ? "Verbal" : "Pre-Verbal"}]
          </span>
        </div>

        <div className="flex-1 bg-white border-2 border-[#808080] border-r-white border-b-white overflow-y-auto p-4 font-['Gulim']">
          <table className="w-full border-collapse text-[12px] border border-black">
            <thead className="bg-[#e0e0e0] sticky top-0 z-10 shadow-sm">
              <tr>
                <th className="border border-black p-1 w-[80px]">영역</th>
                <th className="border border-black p-1 w-[40px]">코드</th>
                <th className="border border-black p-1">항목명</th>
                <th className="border border-black p-1 w-[120px] bg-yellow-50">
                  점수
                </th>
              </tr>
            </thead>
            <tbody>
              {/* SA Section */}
              <tr className="bg-gray-100 font-bold">
                <td colSpan={4} className="border border-black p-1 text-center">
                  사회적 정동 (Social Affect)
                </td>
              </tr>
              {currentItems
                .filter((i) => i.category === "SA")
                .map((item) => (
                  <AdosRow
                    key={item.code}
                    item={item}
                    aiValue={MOCK_AI_RESULTS[item.code]}
                    docValue={doctorScores[item.code] || ""}
                    onChange={handleScoreChange}
                  />
                ))}
              <tr className="bg-[#f0f8ff] font-bold">
                <td
                  colSpan={3}
                  className="border border-black p-1 text-right pr-4"
                >
                  사회적 정동 총합
                </td>
                <td className="border border-black p-1 text-center text-blue-700 text-[14px]">
                  {calculateTotal("SA")}
                </td>
              </tr>

              {/* RRB Section */}
              <tr className="bg-gray-100 font-bold border-t-2 border-black">
                <td colSpan={4} className="border border-black p-1 text-center">
                  제한적이고 반복적인 행동 (RRB)
                </td>
              </tr>
              {currentItems
                .filter((i) => i.category === "RRB")
                .map((item) => (
                  <AdosRow
                    key={item.code}
                    item={item}
                    aiValue={MOCK_AI_RESULTS[item.code]}
                    docValue={doctorScores[item.code] || ""}
                    onChange={handleScoreChange}
                  />
                ))}
              <tr className="bg-[#f0f8ff] font-bold">
                <td
                  colSpan={3}
                  className="border border-black p-1 text-right pr-4"
                >
                  제한적/반복적 행동 총합
                </td>
                <td className="border border-black p-1 text-center text-blue-700 text-[14px]">
                  {calculateTotal("RRB")}
                </td>
              </tr>

              {/* Total Section */}
              <tr className="bg-[#ffe4e1] font-bold border-t-2 border-black">
                <td
                  colSpan={3}
                  className="border border-black p-2 text-right pr-4 text-[13px]"
                >
                  전체 총합 (SA + RRB)
                </td>
                <td className="border border-black p-1 text-center text-red-600 text-[16px]">
                  {calculateTotal("SA") + calculateTotal("RRB")}
                </td>
              </tr>
            </tbody>
          </table>
          {/* [수정] 알림 문구 크기 조정 (20px -> 11px) */}
          <div className="px-1 pb-1 text-[20px] text-blue-800 font-bold shrink-0">
            ※ 'AI' 뱃지가 있는 항목은 AI 분석 점수가 자동 반영되며 수정할 수
            없습니다.
          </div>
        </div>

        <div className="mt-1 flex justify-end gap-1 shrink-0">
          <WindowsButton className="w-[100px] h-[30px]" onClick={onClose}>
            확인
          </WindowsButton>
        </div>
      </div>
    </div>
  );
}

// 개별 행 컴포넌트
function AdosRow({
  item,
  aiValue,
  docValue,
  onChange,
}: {
  item: AdosItemDefinition;
  aiValue: any;
  docValue: string;
  onChange: (code: string, val: string) => void;
}) {
  const hasAiResult = aiValue !== undefined && typeof aiValue === "number";

  return (
    <tr className="hover:bg-blue-50 transition-colors h-[32px]">
      <td className="border border-black p-1 text-center text-gray-500 text-[10px]">
        {item.subCategory === "Communication"
          ? "의사소통"
          : item.subCategory === "Interaction"
            ? "상호작용"
            : "RRB"}
      </td>
      <td className="border border-black p-1 text-center font-bold bg-gray-50">
        {item.code}
      </td>
      <td className="border border-black p-1 pl-2">
        <div className="flex items-center gap-1.5">
          <span>{item.label}</span>
          {item.isAiAnalyzed && (
            <span
              className="text-[9px] font-bold bg-[#E6F0FF] text-[#0055FF] px-1.5 py-[1px] rounded-[4px] border border-[#B3D1FF]"
              title={item.aiSourceTask}
            >
              AI
            </span>
          )}
        </div>
      </td>

      {/* [수정됨] 점수 열의 배경색(td)을 조건부로 변경하여 셀 전체가 회색이 되도록 함 */}
      <td
        className={cn(
          "border border-black p-0",
          hasAiResult ? "bg-gray-200" : "bg-yellow-50",
        )}
      >
        <input
          type="number"
          min="0"
          max="3"
          className={cn(
            "w-full h-full text-center outline-none font-bold bg-transparent", // input 배경은 투명으로 설정
            hasAiResult
              ? "text-blue-700 cursor-not-allowed"
              : "focus:bg-white focus:ring-2 focus:ring-blue-500",
          )}
          value={hasAiResult ? aiValue : docValue}
          readOnly={hasAiResult}
          onChange={(e) => {
            if (!hasAiResult) onChange(item.code, e.target.value);
          }}
        />
      </td>
    </tr>
  );
}
