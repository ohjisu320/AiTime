// src/features/doctor/types/ados.ts

export type AdosCategory = "SA" | "RRB";
export type AdosSubCategory = "Communication" | "Interaction" | "RRB_General";

// 1. ADOS 검사 항목 정의 (Static Data)
export interface AdosItemDefinition {
  code: string;           // UI 표시용 코드 (예: A-2)
  label: string;          // 항목명
  category: AdosCategory;
  subCategory: AdosSubCategory;
  isAiAnalyzed: boolean;  // AI 분석 여부 (뱃지 표시용)
  aiSourceTask?: string;  // 툴팁 설명
}

// 2. AI 분석 결과 데이터 (내부 관리용)
// API DTO(AdosScoresDTO)와는 별개로, UI에서 코드(Key)로 점수에 접근할 때 사용
export interface AdosAiResult {
  [key: string]: number | undefined;
  // ADOS 점수는 0~3점 정수이므로 boolean/string 제거 권장
}