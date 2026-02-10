import { useMemo } from "react";
import { SectionHeader, WindowsButton } from "../layout/WindowsLayout";
import type { AdosDetail } from "@/api/types/examReport.types";
import { MASTER_ADOS_ITEMS, CODES_PRE_VERBAL, CODES_VERBAL } from "../../types/ados";

interface Props {
  onExpandAdos: () => void;
  patientAge: number;
  adosDetail: AdosDetail | null;
}

export default function AiDiagnosisPanel({ onExpandAdos, patientAge, adosDetail }: Props) {
  const scores = adosDetail?.scores;


  // [로직] 환자 연령 및 점수 키 기반으로 Pre-Verbal/Verbal 판단
  // 12~20개월: 무조건 Pre-Verbal
  // 21~30개월: 점수 키에 Verbal 전용 키(예: A-7)가 있으면 Verbal, 없으면 Pre-Verbal
  const moduleType = useMemo(() => {
    if (patientAge <= 20) return "PRE_VERBAL";

    // 21개월 이상일 때: 점수 데이터를 확인
    if (!scores) return "PRE_VERBAL"; // 데이터 없으면 기본값

    // Verbal 전용 키(CODES_VERBAL에만 있고 CODES_PRE_VERBAL에는 없는 키)가 존재하는지 확인
    // 예: A-7 (Pre: A-2), B-7, B-8, B-9
    const verbalSpecificKeys = ["a7", "b7", "b8", "b9", "b16b", "b18"];
    const hasVerbalKey = Object.keys(scores).some(key => verbalSpecificKeys.includes(key.toLowerCase()));

    return hasVerbalKey ? "VERBAL" : "PRE_VERBAL";
  }, [patientAge, scores]);

  const displayKeys = useMemo(() => {
    const targetCodes = moduleType === "PRE_VERBAL" ? CODES_PRE_VERBAL : CODES_VERBAL;
    return targetCodes.map(code => code.replace("-", "").toLowerCase());
  }, [moduleType]);

  // [로직] 총점 색상 결정
  const getTotalColorClass = (total: number) => {
    // 1. 12~20개월 (무조건 Pre-Verbal 기준)
    if (patientAge <= 20) {
      if (total >= 14) return 'text-red-600 border-red-600 bg-red-50';
      if (total >= 10) return 'text-orange-600 border-orange-600 bg-orange-50'; // 10~13
      return 'text-green-600 border-green-600 bg-green-50'; // 0~9
    }

    // 2. 21~30개월
    if (moduleType === 'VERBAL') {
      // Verbal (몇몇 단어 사용)
      if (total >= 12) return 'text-red-600 border-red-600 bg-red-50';
      if (total >= 8) return 'text-orange-600 border-orange-600 bg-orange-50'; // 8~11
      return 'text-green-600 border-green-600 bg-green-50'; // 0~7
    } else {
      // Pre-Verbal (단어 사용 없음) -> 12~20개월 기준과 동일하게 적용 (구체적 언급은 없었으나 통상적용)
      // * 요청 사항: "단어 사용이 거의 밝거나 전혀 없는 21~30개월 아동은 14점 이상..." => 12~20개월과 동일 기준
      if (total >= 14) return 'text-red-600 border-red-600 bg-red-50';
      if (total >= 10) return 'text-orange-600 border-orange-600 bg-orange-50'; // 10~13
      return 'text-green-600 border-green-600 bg-green-50'; // 0~9
    }
  };

  // [헬퍼 함수] API 키(a2)를 기반으로 항목명(Label) 찾기
  const getLabel = (key: string) => {
    const item = MASTER_ADOS_ITEMS.find(
      (i) => i.code.replace("-", "").toLowerCase() === key.toLowerCase()
    );
    return item?.label || "";
  };

  return (
    <div className="h-full bg-[#d4d0c8] flex flex-col font-['Gulim']">
      <SectionHeader title="AI 진단 결과 (ADOS-2)">
        <WindowsButton onClick={onExpandAdos}>상세/수정</WindowsButton>
      </SectionHeader>

      <div className="flex-1 p-3 overflow-y-auto bg-white border border-[#808080] m-1 shadow-inner">
        {!scores ? (
          <div className="text-gray-500 text-center mt-10 text-[13px]">진단 데이터가 없습니다.</div>
        ) : (
          <>
            <div className="mb-6 text-center">
              <span className="text-[14px] font-bold block mb-2">진단 총점</span>
              <div
                className={`text-3xl font-black border-2 py-3 shadow-sm mx-auto w-32
                  ${getTotalColorClass(scores.total ?? 0)}`
                }
              >
                {scores.total ?? '-'}점
              </div>
              <div className="text-[13px] mt-2 text-gray-600">
                (SA: {scores.socialAffectTotal ?? '-'} + RRB: {scores.rrbTotal ?? '-'})
              </div>
            </div>

            <table className="w-full text-[13px] border-collapse border border-[#808080]">
              <thead className="bg-[#f0f0f0]">
                <tr>
                  <th className="border border-[#808080] px-2 py-2 bg-[#e0e0e0] w-[70%] text-left pl-3">항목</th>
                  <th className="border border-[#808080] px-2 py-2 bg-[#e0e0e0] w-[30%]">점수</th>
                </tr>
              </thead>
              <tbody>
                {displayKeys.map((key) => (
                  <tr key={key}>
                    <td className="border border-[#808080] px-3 py-1.5 font-bold bg-[#fafafa]">
                      <div className="flex flex-col">
                        {/* 항목 코드 (예: A2) */}
                        <span className="text-black">{key.toUpperCase()}</span>
                        {/* 항목 명 (예: 목소리를 내는 빈도) - 회색 작은 글씨 */}
                        <span className="text-[11px] font-normal text-gray-500 truncate">
                          {getLabel(key)}
                        </span>
                      </div>
                    </td>
                    <td className="border border-[#808080] px-3 py-1.5 text-center font-bold text-blue-800 text-[14px]">
                      {scores[key as keyof typeof scores] ?? '-'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            <div className="mt-2 text-[12px] text-gray-500 text-right">
              * 환아 연령({patientAge}개월) / {moduleType === 'VERBAL' ? 'Verbal' : 'Pre-Verbal'} 기준 적용
            </div>
          </>
        )}
      </div>
    </div>
  );
}