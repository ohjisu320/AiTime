import { useState, useMemo, useCallback, useEffect, type MouseEvent } from "react";
import { WindowsButton } from "../layout/WindowsLayout";
import { cn } from "@/lib/utils";
// [수정] MASTER_ADOS_ITEMS를 types/ados에서 가져오도록 변경
import { MASTER_ADOS_ITEMS, type AdosItemDefinition, type AdosAiResult } from "../../types/ados";
import type { AdosDetail, AdosScores, AdosUpdateRequest } from "@/api/types/examReport.types";

interface Props {
  onClose: () => void;
  patientAge: number;
  adosDetail?: AdosDetail | null;
  examId?: string;
  onSave?: (examId: string, scores: AdosUpdateRequest) => Promise<void>;
}

// API 키(소문자) ↔ 코드 키(대문자+하이픈) 변환 유틸리티
const apiKeyToCodeKey = (apiKey: string): string => {
  // a2 → A-2, b16b → B-16b, d1 → D-1
  const match = apiKey.match(/^([a-z])(\d+)([a-z]?)$/i);
  if (match) {
    return `${match[1].toUpperCase()}-${match[2]}${match[3]}`;
  }
  return apiKey.toUpperCase();
};

const codeKeyToApiKey = (codeKey: string): string => {
  // A-2 → a2, B-16b → b16b, D-1 → d1
  return codeKey.replace("-", "").toLowerCase();
};

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

// Mock AI 결과 (API 연결 전 폴백)
const MOCK_AI_RESULTS: AdosAiResult = {
  "A-8": 0,
  "B-1": 1,
  "B-4": 0,
  "B-6": 1,
  "B-7": 2,
  "B-18": 1,
  "A-3": 0,
};

export default function AdosModal({ onClose, patientAge, adosDetail, examId, onSave }: Props) {
  const [doctorScores, setDoctorScores] = useState<Record<string, string>>({});
  const [isSaving, setIsSaving] = useState(false);
  const [isVerbal, setIsVerbal] = useState<boolean>(patientAge > 21);

  // 드래그 상태
  const [position, setPosition] = useState({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });

  // API 데이터 사용 여부
  const useApiData = useMemo(() => {
    return adosDetail && adosDetail.scores;
  }, [adosDetail]);

  // API 데이터로부터 점수 변환 (소문자 API 키 → 코드 키)
  const apiScores = useMemo((): Record<string, number> => {
    if (!adosDetail?.scores) return {};

    const result: Record<string, number> = {};
    const scores = adosDetail.scores;

    Object.keys(scores).forEach((apiKey) => {
      const value = scores[apiKey as keyof AdosScores];
      if (typeof value === "number") {
        const codeKey = apiKeyToCodeKey(apiKey);
        result[codeKey] = value;
      }
    });

    return result;
  }, [adosDetail]);

  // API 데이터로 초기 점수 설정
  useEffect(() => {
    if (useApiData && apiScores) {
      const initialScores: Record<string, string> = {};
      Object.keys(apiScores).forEach((codeKey) => {
        const item = MASTER_ADOS_ITEMS.find((i) => i.code === codeKey);
        // AI 분석 항목이 아닌 경우에만 의사 입력 점수로 설정
        if (item && !item.isAiAnalyzed) {
          initialScores[codeKey] = String(apiScores[codeKey]);
        }
      });
      setDoctorScores(initialScores);
    }
  }, [useApiData, apiScores]);

  // 드래그 핸들러
  const handleMouseDown = useCallback((e: MouseEvent<HTMLDivElement>) => {
    setIsDragging(true);
    setDragStart({
      x: e.clientX - position.x,
      y: e.clientY - position.y,
    });
  }, [position]);

  const handleMouseMove = useCallback((e: MouseEvent<HTMLDivElement>) => {
    if (!isDragging) return;
    setPosition({
      x: e.clientX - dragStart.x,
      y: e.clientY - dragStart.y,
    });
  }, [isDragging, dragStart]);

  const handleMouseUp = useCallback(() => {
    setIsDragging(false);
  }, []);

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

  // 점수 가져오기 (API 데이터 또는 Mock 데이터)
  const getScore = (codeKey: string): number | undefined => {
    if (useApiData) {
      return apiScores[codeKey];
    }
    return MOCK_AI_RESULTS[codeKey] as number | undefined;
  };

  const calculateTotal = (category: "SA" | "RRB") => {
    return currentItems
      .filter((item) => item.category === category)
      .reduce((sum, item) => {
        let score = 0;
        const apiScore = getScore(item.code);

        if (item.isAiAnalyzed && typeof apiScore === "number") {
          score = apiScore;
        } else if (
          doctorScores[item.code] !== undefined &&
          doctorScores[item.code] !== ""
        ) {
          score = parseInt(doctorScores[item.code], 10);
        }
        return sum + (isNaN(score) ? 0 : score);
      }, 0);
  };

  // 저장 핸들러
  const handleSave = async () => {
    if (!onSave || !examId) {
      console.warn("onSave 또는 examId가 없습니다.");
      onClose();
      return;
    }

    setIsSaving(true);
    try {
      // 의사 입력 점수를 API 형식으로 변환
      const updateScores: AdosUpdateRequest = {};

      currentItems.forEach((item) => {
        if (!item.isAiAnalyzed && doctorScores[item.code]) {
          const apiKey = codeKeyToApiKey(item.code);
          const score = parseInt(doctorScores[item.code], 10);
          if (!isNaN(score)) {
            (updateScores as Record<string, number>)[apiKey] = score;
          }
        }
      });

      console.log("📤 ADOS 저장 요청:", updateScores);
      await onSave(examId, updateScores);
      onClose();
    } catch (error) {
      console.error("❌ ADOS 저장 실패:", error);
      alert("저장에 실패했습니다. 다시 시도해주세요.");
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
      onClick={onClose}
      onMouseMove={handleMouseMove}
      onMouseUp={handleMouseUp}
      onMouseLeave={handleMouseUp}
    >
      <div
        className="w-[900px] h-[90%] bg-[#d4d0c8] border-2 border-white border-r-[#404040] border-b-[#404040] p-1 flex flex-col shadow-xl"
        style={{
          transform: `translate(${position.x}px, ${position.y}px)`,
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* 드래그 가능한 타이틀바 */}
        <div
          className="bg-[#000080] text-white px-2 py-1 flex justify-between items-center font-bold mb-1 select-none shrink-0"
          style={{ cursor: isDragging ? "grabbing" : "grab" }}
          onMouseDown={handleMouseDown}
        >
          <span>ADOS-2 진단 결과 입력표 (드래그하여 이동)</span>
          <WindowsButton className="text-black" onClick={onClose}>
            X 닫기
          </WindowsButton>
        </div>

        {/* API 데이터 상태 표시 */}
        {!useApiData && (
          <div className="text-[10px] text-orange-600 bg-orange-50 px-2 py-1 border border-orange-200 shrink-0">
            ⚠️ Mock 데이터 사용 중 (API 연결 대기)
          </div>
        )}

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
                    aiValue={getScore(item.code)}
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
                    aiValue={getScore(item.code)}
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
          <div className="px-1 pb-1 text-[11px] text-blue-800 font-bold shrink-0 mt-2">
            ※ 'AI' 뱃지가 있는 항목은 AI 분석 점수가 자동 반영되며 수정할 수
            없습니다.
          </div>
        </div>

        <div className="mt-1 flex justify-end gap-1 shrink-0">
          {onSave && examId && (
            <WindowsButton
              className="w-[100px] h-[30px]"
              onClick={handleSave}
              disabled={isSaving}
            >
              {isSaving ? "저장 중..." : "저장"}
            </WindowsButton>
          )}
          <WindowsButton className="w-[100px] h-[30px]" onClick={onClose}>
            {onSave ? "취소" : "확인"}
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
  aiValue: number | undefined;
  docValue: string;
  onChange: (code: string, val: string) => void;
}) {
  const hasAiResult = item.isAiAnalyzed && aiValue !== undefined && typeof aiValue === "number";

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
            "w-full h-full text-center outline-none font-bold bg-transparent",
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