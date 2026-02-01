// src/features/doctor/api/doctorApi.ts
import api from '@/api/axiosConfig';
// [수정] import type 사용 및 로컬 타입 파일 참조
import type { 
  ApiResponsePatientSearchResponse, 
  PatientDetailFull 
} from '../types/doctor';

export const doctorApi = {
  // [Real API] 환자 검색
  searchPatients: async (params: { page: number; size: number; name?: string }) => {
    // 제네릭 타입에 import한 로컬 타입을 사용
    const { data } = await api.get<ApiResponsePatientSearchResponse>('/doctor/patients', {
      params,
    });
    return data;
  },

  // [Mock API] 특정 환자의 상세 진단 정보 가져오기
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
          height: '112.4cm',
          weight: '20.2kg',
          caregiver: '모 (부 보조)',
          medication: '없음',
          familyHistory: '유 (사촌 형제)',
          history: [
            { category: '출산', content: '38주 미숙아 (2.4kg)' },
            { category: '발달', content: '18개월 독립 보행 시작' },
            { category: '언어', content: '24개월 첫 단어 (현재 문장 불가)' },
            { category: '가족', content: '친가 쪽 언어 발달 지연 가족력' },
          ],
          complaints: [
            { category: '사회성', content: '또래 무리 이탈 현상' },
            { category: '언어', content: 'TV 광고 문구 반복' },
            { category: '행동', content: '상동행동(손 흔들기)' },
            { category: '기타', content: '까치발 보행 관찰' },
          ],
        });
      }, 300);
    });
  },
};