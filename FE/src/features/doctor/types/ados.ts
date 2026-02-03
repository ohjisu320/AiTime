// src/features/doctor/types/ados.ts

export type AdosCategory = "SA" | "RRB"; // SA: 사회적 정동, RRB: 제한/반복 행동
export type AdosSubCategory = "Communication" | "Interaction" | "RRB_General";

// 1. ADOS 검사 항목 정의 (Static Data)
export interface AdosItemDefinition {
  code: string; // 예: A-2, B-1
  label: string; // 예: 가리키기, 유별난 눈맞춤
  category: AdosCategory;
  subCategory: AdosSubCategory;
  isAiAnalyzed: boolean; // 동그라미 표시 여부 (AI 검사 용도)
  aiSourceTask?: string; // 예: "대면호명", "동작모방" (툴팁용)
}

// 2. AI 분석 결과 데이터 (API Response)
export interface AdosAiResult {
  [key: string]: number | boolean | string | undefined;
  // 예: { "A8": 0, "B6": true, "B18": false }
}
