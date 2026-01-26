import { lazy } from 'react';
import type { RouteObject } from 'react-router';

// Lazy Loading을 사용하여 성능을 최적화
const ConsentPage = lazy(() => import('@/domains/exam/pages/ConsentPage'));
const ExamGuidePage = lazy(() => import('@/domains/exam/pages/ExamGuidePage'));
// 추후 구현될 페이지들 예시
// const ExamRecorderPage = lazy(() => import('@/domains/exam/pages/ExamRecorderPage'));

export const jisuRoutes: RouteObject[] = [
  {
    path: "/exam",
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
        element: <ExamGuidePage /> // /exam/guide
      },

   

      // { 
      //   path: "recorder", 
      //   element: <ExamRecorderPage /> // /exam/recorder (실제 검사 녹화)
      // },
    ],
  },
];