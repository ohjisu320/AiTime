import { lazy, Suspense } from 'react';
import type { RouteObject } from 'react-router';
import MobileLayout from '@/components/layout/MobileLayout';
import GlobalErrorPage from '@/components/common/GlobalErrorPage';

// Lazy Loading을 사용하여 성능을 최적화
// 동적 임포트 실패 시 자동으로 페이지를 새로고침하여 최신 청크를 로드
const retryImport = (importFn: () => Promise<any>) => {
  return importFn().catch((error) => {
    console.error('Chunk loading failed, reloading page...', error);
    window.location.reload();
    // 리로드 후 fallback을 반환 (실제로는 리로드되므로 실행되지 않음)
    return { default: () => <div>Loading...</div> };
  });
};

const ConsentPage = lazy(() => retryImport(() => import('@/features/exam/pages/ConsentPage')));
const ExamGuidePage = lazy(() => retryImport(() => import('@/features/exam/pages/ExamGuidePage')));
const MissionListPage = lazy(() => retryImport(() => import('@/features/exam/pages/MissionListPage')));
const ExamRecordingPage = lazy(() => retryImport(() => import('@/features/exam/pages/ExamRecordingPage')));
const ExamGuideVideoPage = lazy(() => retryImport(() => import('@/features/exam/pages/ExamGuideVideoPage')));
const ExamPage = lazy(() => retryImport(() => import('@/features/exam/pages/ExamPage')));
const ExamGuard = lazy(() => retryImport(() => import('@/features/exam/components/ExamGuard')));



const ExamLayout = () => {
  return (
    <Suspense fallback={<div className="flex justify-center items-center h-full">Loading...</div>}>
      <MobileLayout />
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
