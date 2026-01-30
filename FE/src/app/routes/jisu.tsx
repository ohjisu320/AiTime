import { lazy, Suspense } from 'react';
import type { RouteObject } from 'react-router';
import MobileLayout from '@/components/layout/MobileLayout';

// Lazy Loading을 사용하여 성능을 최적화
const ConsentPage = lazy(() => import('@/domains/exam/pages/ConsentPage'));
const ExamGuidePage = lazy(() => import('@/domains/exam/pages/ExamGuidePage'));
const MissionListPage = lazy(() => import('@/domains/exam/pages/MissionListPage'));
const ExamScreeningPage = lazy(() => import('@/domains/exam/pages/ExamRecordingPage'));
const ExamGuideVideoPage = lazy(() => import('@/domains/exam/pages/ExamGuideVideoPage'));
const ExamPage = lazy(() => import('@/domains/exam/pages/ExamPage'));

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
      {
        index: true,
        element: <ConsentPage /> // /exam 접속 시 바로 동의 페이지 노출
      },
      {
        path: "consent",
        element: <ConsentPage /> // /exam/consent
      },
      {
        path: "guide",
        children: [
          {
            index: true,
            element: <ExamGuidePage /> // 👈 /exam/guide (전체 가이드 목록 등) 
          },
          {
            path: ":missionId",
            element: <ExamGuideVideoPage /> // 👈 /exam/guide/1, /exam/guide/2 등 
          }
        ]
      },
      {
        path: "mission",
        element: <MissionListPage />  // 태스크리스트 페이지
      },
      {
        path: "screening/:missionId",
        element: <ExamScreeningPage />
      },

      {
        path: "task/:missionId",
        element: <ExamPage /> // /exam/recorder (실제 검사 진행)
      },
    ],
  }
];
