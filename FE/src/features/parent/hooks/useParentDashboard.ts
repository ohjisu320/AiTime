import { useState, useEffect } from 'react';
import {
  fetchChildHomeInfo,
  type ChildHomeResponse,
  TEST_CHILD_ID,
  MOCK_CASE_AVAILABLE,
} from '../api/dashboardApi';

// ==========================================
// [테스트용 설정]
// 이 값을 true로 하면 아래 MOCK_DATA가 강제로 적용됩니다.
const ENABLE_MOCK = false;

// MOCK_CASE_AVAILABLE를 참조하여, registerInviteCode에서 수정된 내용이 반영되도록 합니다.
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
        // 네트워크 지연 시뮬레이션
        await new Promise(resolve => setTimeout(resolve, 300));
        setData(MOCK_DATA);
        return MOCK_DATA;
      }

      // Get selected child ID from localStorage (support both keys for compatibility)
      const childId = localStorage.getItem('selectedChildId') || localStorage.getItem('childId');

      if (!childId) {
        console.warn('⚠️ No childId in localStorage. Using TEST_CHILD_ID as fallback for development.');
      } else {
        console.log(`✅ Using childId from localStorage: ${childId}`);
      }

      // fetchChildHomeInfo가 이미 linkedHospitals를 포함하고 있으므로
      // 별도로 fetchLinkedHospitals를 호출할 필요 없음
      const response = await fetchChildHomeInfo(childId || TEST_CHILD_ID);

      setData(response);
      return response;
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