import { useState, useMemo } from "react";
import { WindowsButton } from "../layout/WindowsLayout";
import { cn } from "@/lib/utils";
import type { AdosItemDefinition, AdosAiResult } from "../../types/ados";

interface Props {
  onClose: () => void;
  patientAge: number; // [추가] 환자 월령 정보 받기
}

// [전체 통합 항목 리스트 (Master List)]
const MASTER_ADOS_ITEMS: AdosItemDefinition[] = [
  // --- SA: Communication ---
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

  // --- SA: Interaction ---
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

  // --- RRB ---
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

// [그룹 정의]
// Group 1: 12~21개월 OR (21~30개월 & 말 못함)
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

// Group 2: 21~30개월 & 말함
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

  // [상태] 발화 가능 여부 (기본값: 21개월 미만이면 false, 그 이상이면 true)
  const [isVerbal, setIsVerbal] = useState<boolean>(patientAge > 21);

  // [로직] 현재 조건에 맞는 항목 필터링
  const currentItems = useMemo(() => {
    // 12~21개월: 무조건 Pre-Verbal (사용자 정의)
    if (patientAge >= 12 && patientAge <= 21) {
      return MASTER_ADOS_ITEMS.filter((item) =>
        CODES_PRE_VERBAL.includes(item.code),
      );
    }
    // 21~30개월 (그 외): 발화 여부에 따라 결정
    if (isVerbal) {
      return MASTER_ADOS_ITEMS.filter((item) =>
        CODES_VERBAL.includes(item.code),
      );
    } else {
      return MASTER_ADOS_ITEMS.filter((item) =>
        CODES_PRE_VERBAL.includes(item.code),
      );
    }
  }, [patientAge, isVerbal]);

  const handleScoreChange = (code: string, value: string) => {
    setDoctorScores((prev) => ({ ...prev, [code]: value }));
  };

  const calculateTotal = (category: "SA" | "RRB") => {
    return currentItems
      .filter((item) => item.category === category)
      .reduce((sum, item) => {
        const docVal = parseInt(doctorScores[item.code] || "0", 10);
        return sum + (isNaN(docVal) ? 0 : docVal);
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
        {/* 헤더 */}
        <div className="bg-[#000080] text-white px-2 py-1 flex justify-between items-center font-bold mb-1 select-none shrink-0">
          <span>
            ADOS-2 진단 (Module T) - {patientAge}개월 /{" "}
            {isVerbal ? "유창한 말 (Verbal)" : "말 못함 (Pre-Verbal)"}
          </span>
          <WindowsButton onClick={onClose}>X 닫기</WindowsButton>
        </div>

        {/* [추가] 조건 설정 툴바 (21개월 이상일 때만 노출하거나 항상 노출) */}
        <div className="bg-[#f0f0f0] border border-[#808080] p-2 mb-1 flex items-center gap-4 text-[12px]">
          <span className="font-bold">검사 기준 설정:</span>
          <label className="flex items-center gap-1 cursor-pointer">
            <input
              type="checkbox"
              checked={isVerbal}
              onChange={(e) => setIsVerbal(e.target.checked)}
              disabled={patientAge <= 21} // 21개월 이하는 수정 불가 (규정상)
            />
            <span>발화 가능 (21~30개월 기준)</span>
          </label>
          <span className="text-gray-500 text-[11px] ml-auto">
            ※ 현재 월령({patientAge}개월)에 맞춰{" "}
            {isVerbal ? "Group 2 (말하는 아동)" : "Group 1 (말 못하는 아동)"}{" "}
            항목이 적용되었습니다.
          </span>
        </div>

        {/* 테이블 */}
        <div className="flex-1 bg-white border-2 border-[#808080] border-r-white border-b-white overflow-y-auto p-4 font-['Gulim']">
          <table className="w-full border-collapse text-[12px] border border-black">
            <thead className="bg-[#e0e0e0] sticky top-0 z-10 shadow-sm">
              <tr>
                <th className="border border-black p-1 w-[80px]">영역</th>
                <th className="border border-black p-1 w-[40px]">코드</th>
                <th className="border border-black p-1">항목명</th>
                <th className="border border-black p-1 w-[80px] bg-blue-50 text-blue-800">
                  AI 분석
                </th>
                <th className="border border-black p-1 w-[120px] bg-yellow-50">
                  전문의 판정
                </th>
              </tr>
            </thead>
            <tbody>
              {/* SA Section */}
              <tr className="bg-gray-100 font-bold">
                <td colSpan={5} className="border border-black p-1 text-center">
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
                <td className="border border-black p-1 bg-gray-200"></td>
                <td className="border border-black p-1 text-center text-blue-700 text-[14px]">
                  {calculateTotal("SA")}
                </td>
              </tr>

              {/* RRB Section */}
              <tr className="bg-gray-100 font-bold border-t-2 border-black">
                <td colSpan={5} className="border border-black p-1 text-center">
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
                <td className="border border-black p-1 bg-gray-200"></td>
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
                <td className="border border-black p-1 bg-gray-200"></td>
                <td className="border border-black p-1 text-center text-red-600 text-[16px]">
                  {calculateTotal("SA") + calculateTotal("RRB")}
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <div className="mt-1 flex justify-end gap-1 shrink-0">
          <WindowsButton className="w-[100px] h-[30px]" onClick={onClose}>
            취소
          </WindowsButton>
          <WindowsButton className="w-[100px] h-[30px] font-bold text-blue-900">
            저장
          </WindowsButton>
        </div>
      </div>
    </div>
  );
}

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
  const formatAiValue = (val: any) =>
    val === undefined ? "-" : val === true ? "T" : val === false ? "F" : val;
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
              title={item.aiSourceTask || "AI 자동 분석 항목"}
            >
              AI
            </span>
          )}
        </div>
      </td>
      <td
        className={cn(
          "border border-black p-1 text-center font-mono font-bold",
          aiValue !== undefined ? "text-blue-700 bg-blue-50" : "text-gray-300",
        )}
      >
        {formatAiValue(aiValue)}
      </td>
      <td className="border border-black p-0">
        <input
          type="number"
          min="0"
          max="3"
          className="w-full h-full text-center outline-none bg-yellow-50 focus:bg-white focus:ring-2 focus:ring-blue-500 font-bold"
          placeholder={
            aiValue !== undefined && typeof aiValue === "number"
              ? aiValue.toString()
              : ""
          }
          value={docValue}
          onChange={(e) => onChange(item.code, e.target.value)}
        />
      </td>
    </tr>
  );
}
