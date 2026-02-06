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
const ENABLE_MOCK = false; // Swagger 토큰으로 실제 API 테스트

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
      setIsError(false);

      if (ENABLE_MOCK) {
        // 네트워크 지연 시뮬레이션
        await new Promise(resolve => setTimeout(resolve, 300));
        setData(MOCK_DATA);
        return MOCK_DATA;
      }

      // Get child ID from localStorage
      // Priority: manually set 'childId' > profile-selected 'selectedChildId'
      const childId = localStorage.getItem('selectedChildId') || localStorage.getItem('childId');

      if (!childId) {
        console.warn('⚠️ No childId in localStorage. Using TEST_CHILD_ID as fallback for development.');
      } else {
        console.log(`✅ Using childId from localStorage: ${childId}`);
      }

      // API 호출 - 응답이 올 때까지 무한정 대기
      const response = await fetchChildHomeInfo(childId || TEST_CHILD_ID);

      // ✅ 디버깅: API 응답 전체 구조 확인
      console.log('📦 [API Response] Full response:', response);
      console.log('📦 [API Response] examId:', response.examId);
      console.log('📦 [API Response] examStatus:', response.examStatus);
      console.log('📦 [API Response] examId type:', typeof response.examId);

      // ✅ examId 처리: 상태에 따라 저장 또는 삭제
      if (response.examId) {
        localStorage.setItem('examId', response.examId);
        console.log(`✅ examId 저장: ${response.examId}`);
      } else {
        // examId가 없으면 (AVAILABLE 상태 등) 기존 examId 삭제
        const oldExamId = localStorage.getItem('examId');
        if (oldExamId) {
          localStorage.removeItem('examId');
          console.log(`🗑️ 이전 examId 삭제: ${oldExamId}`);
        }
        console.log('⚠️ examId가 없습니다. (AVAILABLE 상태일 수 있음)');
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