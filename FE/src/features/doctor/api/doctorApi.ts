// src/features/doctor/api/doctorApi.ts
import api from '@/api/axiosConfig';
import type {
  ApiResponsePatientSearchResponse,
  PatientDetailFull,
  PatientDto
} from '../types/doctor';

// 랜덤 더미 데이터 세트
const DUMMY_DATA = {
  heights: ['95.2cm', '98.5cm', '102.3cm', '105.8cm', '110.2cm', '112.4cm'],
  weights: ['14.5kg', '16.2kg', '18.0kg', '20.2kg', '22.5kg', '24.0kg'],
  caregivers: ['모', '부', '모 (부 보조)', '부 (모 보조)', '조부모', '모 (조모 보조)'],
  medications: ['없음', '없음', '없음', '비타민D', '철분 보조제', '알레르기약'],
  familyHistories: ['없음', '없음', '친가 형제 언어 지연', '모계 ASD 의심', '부계 ADHD 가족력', '유 (사촌 형제)'],
  histories: [
    [
      { category: '출산', content: '38주 정상 분만 (3.2kg)' },
      { category: '발달', content: '12개월 독립 보행' },
    ],
    [
      { category: '출산', content: '40주 정상 분만 (3.5kg)' },
      { category: '발달', content: '14개월 독립 보행' },
      { category: '언어', content: '18개월 첫 단어' },
    ],
    [
      { category: '출산', content: '38주 미숙아 (2.4kg)' },
      { category: '발달', content: '18개월 독립 보행 시작' },
      { category: '언어', content: '24개월 첫 단어 (현재 문장 불가)' },
      { category: '가족', content: '친가 쪽 언어 발달 지연 가족력' },
    ],
    [
      { category: '출산', content: '39주 제왕절개 (3.0kg)' },
      { category: '발달', content: '10개월 독립 보행' },
      { category: '언어', content: '12개월 첫 단어' },
    ],
  ],
  complaints: [
    [
      { category: '사회성', content: '또래 상호작용 어려움' },
      { category: '언어', content: '반향어 관찰' },
    ],
    [
      { category: '사회성', content: '눈 맞춤 회피' },
      { category: '행동', content: '반복적인 손 흔들기' },
      { category: '기타', content: '특정 소리에 민감' },
    ],
    [
      { category: '사회성', content: '또래 무리 이탈 현상' },
      { category: '언어', content: 'TV 광고 문구 반복' },
      { category: '행동', content: '상동행동(손 흔들기)' },
      { category: '기타', content: '까치발 보행 관찰' },
    ],
    [
      { category: '언어', content: '언어 발달 지연' },
      { category: '행동', content: '물건 줄 세우기' },
    ],
  ],
};

// 랜덤 선택 헬퍼
const pickRandom = <T>(arr: T[]): T => arr[Math.floor(Math.random() * arr.length)];

export const doctorApi = {
  // [Real API] 월별 예약 캘린더 조회
  getReservationCalendar: async (year: number, month: number): Promise<string[]> => {
    console.log(`📅 [API] 예약 캘린더 조회: ${year}-${month}`);
    const { data } = await api.get<{
      code: number;
      status: string;
      message: string;
      data: { data: string[] };
    }>('/doctor/reservations/calendar', {
      params: { year, month },
    });
    // data.data.data 형태로 날짜 배열 반환
    return data.data?.data || [];
  },

  // [Real API] 환자 검색
  searchPatients: async (params: {
    page: number;
    size: number;
    date?: string;        // YYYY-MM-DD
    year?: number;
    month?: number;
    day?: number;
    name?: string;
    resultStatus?: string;
    effectiveDate?: string; // YYYY-MM-DD
  }) => {
    const { data } = await api.get<ApiResponsePatientSearchResponse>('/doctor/patients', {
      params,
    });
    return data;
  },

  // API 데이터 + 랜덤 더미 데이터 믹싱하여 상세 정보 생성
  getPatientDetailFromDto: (patient: PatientDto): PatientDetailFull => {
    return {
      ...patient,
      height: pickRandom(DUMMY_DATA.heights),
      weight: pickRandom(DUMMY_DATA.weights),
      caregiver: pickRandom(DUMMY_DATA.caregivers),
      medication: pickRandom(DUMMY_DATA.medications),
      familyHistory: pickRandom(DUMMY_DATA.familyHistories),
      history: pickRandom(DUMMY_DATA.histories),
      complaints: pickRandom(DUMMY_DATA.complaints),
    };
  },

  // [Mock API] 특정 환자의 상세 진단 정보 가져오기 (하드코딩 버전 - 기존 호환용)
  getPatientDetail: async (childId: string): Promise<PatientDetailFull> => {
    return new Promise((resolve) => {
      setTimeout(() => {
        resolve({
          childId,
          userId: 'user-uuid',
          name: '박지민',
          monthlyAge: 72,
          birthdate: '2020-05-12',
          gender: 'MALE',
          latestExamStatus: 'COMPLETED',
          height: pickRandom(DUMMY_DATA.heights),
          weight: pickRandom(DUMMY_DATA.weights),
          caregiver: pickRandom(DUMMY_DATA.caregivers),
          medication: pickRandom(DUMMY_DATA.medications),
          familyHistory: pickRandom(DUMMY_DATA.familyHistories),
          history: pickRandom(DUMMY_DATA.histories),
          complaints: pickRandom(DUMMY_DATA.complaints),
        });
      }, 300);
    });
  },
};