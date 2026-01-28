import { useState, useEffect } from 'react';
import {
  fetchChildHomeInfo,
  type ChildHomeResponse,
  MOCK_CASE_AVAILABLE,
  MOCK_CASE_NEED_HOSPITAL,
  MOCK_CASE_COOLDOWN,
  MOCK_CASE_COOLDOWN_BEFORE,
  MOCK_CASE_IN_PROGRESS
} from '../api/dashboardApi';

// ==========================================
// [테스트용 설정]
// 이 값을 true로 하면 아래 MOCK_DATA가 강제로 적용됩니다.
const ENABLE_MOCK = true;

// MOCK_CASE_AVAILABLE를 참조하여, registerInviteCode에서 수정된 내용이 반영되도록 합니다.
// 필요에 따라 다른 케이스(MOCK_CASE_NEED_HOSPITAL 등)로 교체하여 테스트하세요.
const MOCK_DATA = MOCK_CASE_AVAILABLE.data;
// ==========================================

export const useParentDashboard = () => {
  const [data, setData] = useState<ChildHomeResponse['data'] | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isError, setIsError] = useState(false);

  const fetchData = async () => {
    try {
      setIsLoading(true);

      if (ENABLE_MOCK) {
        // 네트워크 지연 시뮬레이션 (선택사항, 너무 빠르면 로딩 못볼 수 있으므로 300ms 줌)
        await new Promise(resolve => setTimeout(resolve, 300));
        setData(MOCK_DATA);
        return MOCK_DATA;
      }

      // fetchChildHomeInfo handles errors and returns mock data, so this should almost always succeed
      const response = await fetchChildHomeInfo("child-001");
      setData(response.data);
      return response.data; // Return data for chaining
    } catch (err) {
      console.error("Unexpected error in useParentDashboard", err);
      setIsError(true);
      return null;
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  return {
    data,
    isLoading,
    isError,
    refetch: fetchData,
  };
};