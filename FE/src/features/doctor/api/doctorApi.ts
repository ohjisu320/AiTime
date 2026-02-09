// src/features/doctor/api/doctorApi.ts
import api from '@/api/axiosConfig';
import type {
  ApiResponsePatientSearchResponse,
  PatientDetailFull,
  PatientDto
} from '../types/doctor';

// 랜덤 더미 데이터 세트
const DUMMY_DATA = {
  heights: ['79.5cm', '82.3cm', '85.1cm', '88.4cm', '92.0cm', '95.5cm'],
  weights: ['10.2kg', '11.5kg', '12.1kg', '13.4kg', '14.2kg', '15.0kg'],
  caregivers: ['모', '부', '모 (부 보조)', '부 (모 보조)', '조부모', '모 (조모 보조)'],
  medications: ['없음', '없음', '없음', '비타민D', '철분제', '감기약 복용 중'],
  familyHistories: ['없음', '없음', '친가 형제 언어 지연', '모계 자폐 스펙트럼 의심', '부계 ADHD 가족력', '사촌 형제 발달 지연'],
  histories: [
    [
      { category: '출산', content: '39주 정상 분만 (3.2kg)' },
      { category: '발달', content: '13개월 독립 보행' },
    ],
    [
      { category: '출산', content: '38주 제왕절개 (2.9kg)' },
      { category: '발달', content: '15개월 걷기 시작' },
      { category: '언어', content: '18개월 첫 단어 (엄마)' },
    ],
    [
      { category: '출산', content: '36주 조산 (2.4kg), 인큐베이터 2주' },
      { category: '발달', content: '18개월 독립 보행 (다소 늦음)' },
      { category: '질환', content: '잦은 중이염' },
    ],
    [
      { category: '출산', content: '40주 자연분만 (3.4kg)' },
      { category: '발달', content: '12개월 보행, 14개월 옹알이' },
      { category: '기타', content: '24개월 경 열성 경련 1회' },
    ],
  ],
  complaints: [
    [
      { category: '사회성', content: '이름을 불러도 전혀 쳐다보지 않아요' },
      { category: '언어', content: '말을 걸어도 반응이 없고 혼자 노는 것 같아요' },
    ],
    [
      { category: '사회성', content: '눈 맞춤이 1-2초 내로 짧고 피해요' },
      { category: '행동', content: '기분이 좋으면 손을 파닥거려요' },
      { category: '감각', content: '헤어드라이어 소리에 귀를 막고 자지러져요' },
    ],
    [
      { category: '사회성', content: '엄마가 나가도 찾지 않고 무관심해요' },
      { category: '언어', content: '의미 없는 소리(옹알이)만 계속 해요' },
      { category: '행동', content: '까치발로 걷는 모습이 자주 보여요' },
      { category: '놀이', content: '자동차 바퀴만 계속 돌리고 있어요' },
    ],
    [
      { category: '언어', content: '원하는 게 있으면 말 대신 손을 잡아 끌어요' },
      { category: '행동', content: '제자리에서 빙글빙글 도는 행동을 해요' },
      { category: '언어', content: '네/아니오 대답을 못하고 질문을 따라해요(반향어)' },
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
      // 1. DTO 필드 복사 (hospitalChildrenId, gender 등)
      ...patient,

      // 2. [수정] DTO 필드 -> UI 필드 명시적 매핑 (에러 해결)
      name: patient.childName,       // childName -> name
      monthlyAge: patient.months,    // months -> monthlyAge

      // 3. 필수 필드 보완 (API에 없는 경우 기본값)
      birthdate: patient.birthdate || "2023-01-01",

      // 4. 더미 데이터 추가
      height: pickRandom(DUMMY_DATA.heights),
      weight: pickRandom(DUMMY_DATA.weights),
      caregiver: pickRandom(DUMMY_DATA.caregivers),
      medication: pickRandom(DUMMY_DATA.medications),
      familyHistory: pickRandom(DUMMY_DATA.familyHistories),
      history: pickRandom(DUMMY_DATA.histories),
      complaints: pickRandom(DUMMY_DATA.complaints),
    };
  },

  // [Mock API] 특정 환자의 상세 진단 정보 가져오기 (하드코딩 버전)
  getPatientDetail: async (childId: string): Promise<PatientDetailFull> => {
    return new Promise((resolve) => {
      setTimeout(() => {
        resolve({
          // [수정] PatientDetailFull 타입 준수 (userId 제거, hospitalChildrenId 추가)
          hospitalChildrenId: 'mock-hospital-child-id',
          childId,
          // userId: 'user-uuid', // [삭제] 타입 정의에 없으므로 제거

          name: '박지민',        // UI용 필드
          monthlyAge: 72,       // UI용 필드
          birthdate: '2020-05-12',
          gender: 'MALE',
          // latestExamStatus: 'COMPLETED', // PatientDto에 없으면 제거하거나 타입에 추가 필요 (현재 DTO엔 없음)

          // 더미 데이터
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