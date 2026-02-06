import { lazy, Suspense } from 'react';
import type { RouteObject } from 'react-router';
import MobileLayout from '@/components/layout/MobileLayout';

// Lazy Loading을 사용하여 성능을 최적화
const ConsentPage = lazy(() => import('@/features/exam/pages/ConsentPage'));
const ExamGuidePage = lazy(() => import('@/features/exam/pages/ExamGuidePage'));
const MissionListPage = lazy(() => import('@/features/exam/pages/MissionListPage'));
const ExamRecordingPage = lazy(() => import('@/features/exam/pages/ExamRecordingPage'));
const ExamGuideVideoPage = lazy(() => import('@/features/exam/pages/ExamGuideVideoPage'));
const ExamPage = lazy(() => import('@/features/exam/pages/ExamPage'));
const ExamGuard = lazy(() => import('@/features/exam/components/ExamGuard'));



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
