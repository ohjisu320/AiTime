import { RouterProvider } from 'react-router-dom';
import { router } from './routes'; // 우리가 만든 routes/index.tsx 연결

function App() {
  return <RouterProvider router={router} />;
}

export default App;