import { useMemo } from "react";
import { SectionHeader, WindowsButton } from "../layout/WindowsLayout";
import type { AdosDetail } from "@/api/types/examReport.types";

interface Props {
  onExpandAdos: () => void;
  patientAge: number;
  adosDetail: AdosDetail | null;
}

export default function AiDiagnosisPanel({ onExpandAdos, patientAge, adosDetail }: Props) {
  const isUnder21 = patientAge < 21;
  // 수정 1: '|| {}' 제거. 데이터가 없으면 undefined 상태로 둡니다.
  const scores = adosDetail?.scores;

  const displayKeys = useMemo(() => {
    if (isUnder21) {
      return ["a2", "a8", "b1", "b4", "b5", "b6", "b12", "b13", "b14", "b15"];
    } else {
      return ["a7", "b1", "b4", "b5", "b7", "b8", "b9", "b13", "b15", "b16b", "b18"];
    }
  }, [isUnder21]);

  return (
    <div className="h-full bg-[#d4d0c8] flex flex-col font-['Gulim']">
      <SectionHeader title="AI 진단 결과 (ADOS-2)">
        <WindowsButton onClick={onExpandAdos}>상세/수정</WindowsButton>
      </SectionHeader>

      <div className="flex-1 p-2 overflow-y-auto bg-white border border-[#808080] m-1">
        {/* scores가 없으면 데이터 없음 처리 */}
        {!scores ? (
          <div className="text-gray-500 text-center mt-10">진단 데이터가 없습니다.</div>
        ) : (
          <>
            <div className="mb-4 text-center">
              <span className="text-sm font-bold block mb-1">진단 총점</span>
              {/* 수정 2: scores가 존재함을 확인했으므로 ?. 사용 혹은 접근 가능하나 안전하게 ?. 사용 */}
              <div className={`text-2xl font-black border-2 py-2 ${scores.total >= 8 ? 'text-red-600 border-red-600 bg-red-50' : 'text-green-600 border-green-600 bg-green-50'}`}>
                {scores.total ?? '-'}점
              </div>
              <div className="text-[11px] mt-1 text-gray-600">
                {/* 수정 3: 개별 속성 접근 시 옵셔널 체이닝 적용 */}
                (SA: {scores.socialAffectTotal ?? '-'} + RRB: {scores.rrbTotal ?? '-'})
              </div>
            </div>

            <table className="w-full text-[11px] border-collapse border border-[#808080]">
              <thead className="bg-[#f0f0f0]">
                <tr>
                  <th className="border border-[#808080] px-1 py-1">항목</th>
                  <th className="border border-[#808080] px-1 py-1">점수</th>
                </tr>
              </thead>
              <tbody>
                {displayKeys.map((key) => (
                  <tr key={key}>
                    <td className="border border-[#808080] px-2 py-1 font-bold bg-[#fafafa]">
                      {key.toUpperCase()}
                    </td>
                    <td className="border border-[#808080] px-2 py-1 text-center">
                      {/* 수정 4: string 타입인 key를 scores의 key로 타입 단언(Type Assertion) */}
                      {scores[key as keyof typeof scores] ?? '-'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            <div className="mt-2 text-[10px] text-gray-500 text-right">
              * 환아 연령({patientAge}개월) 기준 적용
            </div>
          </>
        )}
      </div>
    </div>
  );
}