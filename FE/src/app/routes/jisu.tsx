import { lazy, Suspense } from 'react';
import type { RouteObject } from 'react-router';
import MobileLayout from '@/components/layout/MobileLayout';
import GlobalErrorPage from '@/components/common/GlobalErrorPage';

// Lazy Loading을 사용하여 성능을 최적화
// 동적 임포트 실패 시 자동으로 페이지를 새로고침하여 최신 청크를 로드 (무한 루프 방지)
const retryImport = async (importFn: () => Promise<any>) => {
  try {
    return await importFn();
  } catch (error: any) {
    console.error('Chunk loading failed:', error);

    // 이미 리로드했는지 확인
    const isReloaded = sessionStorage.getItem('chunk_reload');

    if (!isReloaded) {
      console.log('Reloading page to fetch new chunks...');
      sessionStorage.setItem('chunk_reload', 'true');
      window.location.reload();
      return new Promise(() => { }); // 리로드 중이므로 대기
    }

    // 이미 리로드했는데도 에러가 나면 에러 전파 (무한 루프 방지)
    sessionStorage.removeItem('chunk_reload'); // 다음 시도를 위해 초기화
    throw error;
  }
};

const ConsentPage = lazy(() => retryImport(() => import('@/features/exam/pages/ConsentPage')));
const ExamGuidePage = lazy(() => retryImport(() => import('@/features/exam/pages/ExamGuidePage')));
const MissionListPage = lazy(() => retryImport(() => import('@/features/exam/pages/MissionListPage')));
const ExamRecordingPage = lazy(() => retryImport(() => import('@/features/exam/pages/ExamRecordingPage')));
const ExamGuideVideoPage = lazy(() => retryImport(() => import('@/features/exam/pages/ExamGuideVideoPage')));
const ExamPage = lazy(() => retryImport(() => import('@/features/exam/pages/ExamPage')));
const ExamGuard = lazy(() => retryImport(() => import('@/features/exam/components/ExamGuard')));



import { useLocation } from 'react-router-dom';

const ExamLayout = () => {
  const location = useLocation();
  const isGuidePage = location.pathname.includes('/guide');

  return (
    <Suspense fallback={<div className="flex justify-center items-center h-full">Loading...</div>}>
      <MobileLayout className={isGuidePage ? "bg-gray-50" : ""} />
    </Suspense>
  );
};

export const jisuRoutes: RouteObject[] = [
  {
    path: "/exam",
    element: <ExamLayout />, // 최상위에서 MobileLayout 적용
    errorElement: <GlobalErrorPage />, // ✅ 전역 에러 페이지 추가
    children: [
      // 1. Consent Page (examId가 있으면 리다이렉트)
      {
        element: <ExamGuard requireExamId={false} redirectIfExamIdExists={true} />,
        children: [
          {
            index: true,
            element: <ConsentPage />
          },
          {
            path: "consent",
            element: <ConsentPage />
          },
        ]
      },

      // 2. Guide and Mission pages (no examId guard - navigation controlled by examStatus)
      {
        path: "guide",
        children: [
          {
            index: true,
            element: <ExamGuidePage />
          },
          {
            path: ":missionId",
            element: <ExamGuideVideoPage />
          }
        ]
      },
      {
        path: "mission",
        element: <MissionListPage />
      },

      // 3. Protected Routes (examId required for actual exam execution)
      {
        element: <ExamGuard requireExamId={true} />,
        children: [
          {
            path: "screening/:missionId",
            element: <ExamRecordingPage />
          },
          {
            path: "task/:missionId",
            element: <ExamPage />
          },
        ]
      }
    ],
  }
];
