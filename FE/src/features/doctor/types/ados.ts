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
}

// [추가] 모든 ADOS 항목 마스터 데이터 (이곳에서 중앙 관리)
export const MASTER_ADOS_ITEMS: AdosItemDefinition[] = [
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