// src/App.tsx
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { RouterProvider } from 'react-router-dom';
import { router } from './routes'; // 기존 라우터 연결


// 1. QueryClient 인스턴스를 생성합니다. 
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1, // 통신 실패 시 1번 더 시도합니다.
      refetchOnWindowFocus: false, // 다른 창 갔다가 돌아왔을 때 자동 새로고침 방지
    },
  },
});

import { Toaster } from "@/components/ui/sonner";

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <RouterProvider router={router} />
      <Toaster />
    </QueryClientProvider>
  );
}
export default App;
