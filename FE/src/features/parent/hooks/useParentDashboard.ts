// import { useQuery } from '@tanstack/react-query'; // 나중에 연동 시 사용
// import axios from '@/utils/axios';

interface LinkedHospital {
  hospitalId: string;
  name: string;
}

interface DashboardData {
  childId: string;
  name: string;
  gender: 'MALE' | 'FEMALE';
  isExamEligible: boolean;
  examProgress: number; 
  hasPreviousExam: boolean;
  nextEligibleAt: string;
  linkedHospitals: LinkedHospital[];
}

export const useParentDashboard = () => {
  // 1. 가짜 데이터 정의
  const mockData: DashboardData = {
    childId: "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    name: "오지수", // 일단 나...
    gender: "MALE",
    isExamEligible: true,
    examProgress: 2,
    hasPreviousExam: true,
    nextEligibleAt: "2026-05-30",
    linkedHospitals: [
      { hospitalId: "1", name: "서울아이소아과" },
      { hospitalId: "2", name: "세브란스 병원" }
    ]
  };

  // 2. DashboardPage에서 사용하는 변수들과 형식을 맞춰서 반환
  return {
    data: mockData,
    isLoading: false,
    isError: false,
  };
};