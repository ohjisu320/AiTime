import { useMemo } from "react";
import { SectionHeader, WindowsButton } from "../layout/WindowsLayout";
import type { AdosDetail } from "@/api/types/examReport.types";
// [추가] 항목명 매핑을 위해 MASTER_ADOS_ITEMS import
import { MASTER_ADOS_ITEMS } from "../../types/ados";

interface Props {
  onExpandAdos: () => void;
  patientAge: number;
  adosDetail: AdosDetail | null;
}

export default function AiDiagnosisPanel({ onExpandAdos, patientAge, adosDetail }: Props) {
  const isUnder21 = patientAge < 21;
  const scores = adosDetail?.scores;

  const displayKeys = useMemo(() => {
    if (isUnder21) {
      return ["a2", "a8", "b1", "b4", "b5", "b6", "b12", "b13", "b14", "b15"];
    } else {
      return ["a7", "b1", "b4", "b5", "b7", "b8", "b9", "b13", "b15", "b16b", "b18"];
    }
  }, [isUnder21]);

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
                  ${(scores.total ?? 0) >= 8
                    ? 'text-red-600 border-red-600 bg-red-50'
                    : 'text-green-600 border-green-600 bg-green-50'}`
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
              * 환아 연령({patientAge}개월) 기준 적용
            </div>
          </>
        )}
      </div>
    </div>
  );
}