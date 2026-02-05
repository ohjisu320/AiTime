import { useState, useEffect } from 'react';
import {
  fetchChildHomeInfo,
  type ChildHomeData,
  TEST_CHILD_ID,
} from '../api/dashboardApi';

export const useParentDashboard = () => {
  const [data, setData] = useState<ChildHomeData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isError, setIsError] = useState(false);

  const fetchData = async () => {
    try {
      setIsLoading(true);
      setIsError(false);


      // Get child ID from localStorage
      // Priority: manually set 'childId' > profile-selected 'selectedChildId'
      const childId = localStorage.getItem('selectedChildId');

      if (!childId) {
        console.warn('⚠️ No childId in localStorage. Using TEST_CHILD_ID as fallback for development.');
      } else {
        console.log(`✅ Using childId from localStorage: ${childId}`);
      }

      // API 호출 - 응답이 올 때까지 무한정 대기
      const response = await fetchChildHomeInfo(childId || TEST_CHILD_ID);

      // ✅ examId가 있으면 localStorage에 저장 (검사 세션에서 사용)
      if (response.examId) {
        localStorage.setItem('examId', String(response.examId));
        console.log(`✅ examId 저장: ${response.examId}`);
      } else {
        console.warn('⚠️ examId가 없습니다.');
      }

      setData(response);
      return response;
    } catch (err) {
      console.error("Error in useParentDashboard", err);
      setIsError(true);
      setData(null);
      return null;
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    // AbortController로 중복 호출 방지
    const abortController = new AbortController();
    let isMounted = true;

    const loadData = async () => {
      if (!isMounted) return;
      await fetchData();
    };

    loadData();

    // Cleanup: 컴포넌트 언마운트 시 실행
    return () => {
      isMounted = false;
      abortController.abort();
    };
  }, []); // 빈 배열: 마운트 시 한 번만 실행

  return {
    data,
    isLoading,
    isError,
    refetch: fetchData,
  };
};