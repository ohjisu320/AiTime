// src/features/parent/types/dashboard.ts
export interface LinkedHospital {
  hospitalId: string;
  name: string;
}

export interface DashboardData {
  childId: string;
  name: string;
  gender: 'MALE' | 'FEMALE';
  isExamEligible: boolean;   // READY 상태 여부
  examProgress: number;      // 0~4단계 미션
  hasPreviousExam: boolean;
  nextEligibleAt: string;    // 날짜 데이터
  linkedHospitals: LinkedHospital[];
}


