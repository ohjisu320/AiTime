import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';

export default function LoginPage() {
  const navigate = useNavigate();
  const [role, setRole] = useState<'parent' | 'doctor' | 'reception'>('parent');

  const handleLogin = (e: React.FormEvent) => {
    e.preventDefault();
    if (role === 'parent') navigate('/parent/dashboard');
    else if (role === 'doctor') navigate('/doctor/dashboard');
    else navigate('/reception');
  };

  return (
    // 1. 배경: 은은한 보라색 그라데이션
    <div className="min-h-screen w-full flex items-center justify-center bg-gradient-to-b from-white to-[#9D8AD6] p-4">
      
      {/* 2. 카드: 컴팩트한 사이즈 */}
      <div className="w-full max-w-[480px] bg-white rounded-[40px] shadow-[0px_0px_40px_10px_rgba(157,138,214,0.3)] p-8 md:p-10 relative overflow-hidden">
        
        {/* 로고 영역 */}
        <div className="flex flex-col items-center mb-8">
          <div className="w-16 h-16 bg-gray-100 rounded-2xl mb-3 flex items-center justify-center">
             <span className="text-2xl">👶</span>
          </div>
          <h1 className="text-4xl font-bold text-gray-900 font-['DM_Sans'] tracking-tight">AiTime</h1>
        </div>

        {/* 3. 역할 선택 탭 */}
        <div className="flex bg-gray-100 p-1 rounded-2xl mb-8">
          {(['parent', 'doctor', 'reception'] as const).map((r) => (
            <button
              key={r}
              type="button"
              onClick={() => setRole(r)}
              className={`flex-1 py-3 text-sm font-bold rounded-xl transition-all duration-200 ${
                role === r
                  ? 'bg-[#9D8AD6] text-white shadow-sm' // 선택됨
                  : 'text-gray-400 hover:text-gray-600'   // 선택 안됨
              }`}
            >
              {r === 'parent' ? '부모' : r === 'doctor' ? '의료진' : '접수처'}
            </button>
          ))}
        </div>

        {/* 4. 입력 폼 */}
        <form onSubmit={handleLogin} className="space-y-6">
          <div className="space-y-2">
            <Label className="text-base font-bold text-gray-700 ml-1">이메일</Label>
            <Input 
              type="email" 
              placeholder="example@email.com"
              className="h-12 bg-gray-50 border-gray-200 rounded-xl focus:border-[#9D8AD6] focus:ring-[#9D8AD6]" 
            />
          </div>

          <div className="space-y-2">
            <Label className="text-base font-bold text-gray-700 ml-1">비밀번호</Label>
            <Input 
              type="password" 
              placeholder="••••••••" 
              className="h-12 bg-gray-50 border-gray-200 rounded-xl focus:border-[#9D8AD6] focus:ring-[#9D8AD6]" 
            />
          </div>

          {/* 로그인 버튼 */}
          <Button 
            type="submit" 
            className="w-full h-14 bg-[#9D8AD6] hover:bg-[#8b7ad6] text-white text-lg font-bold rounded-xl shadow-lg shadow-[#9D8AD6]/30 mt-2"
          >
            로그인
          </Button>
        </form>

        {/* 5. 하단 링크들 (여기가 핵심! ✨) */}
        <div className="mt-8 space-y-3">
          
          {/* ✅ [수정됨] 부모(parent)일 때만 회원가입 버튼 표시 */}
          {role === 'parent' && (
            <>
              <div className="relative flex items-center justify-center">
                 <div className="border-t border-gray-200 w-full absolute"></div>
                 <span className="bg-white px-3 text-xs text-gray-400 relative z-10">또는</span>
              </div>

              <Button 
                variant="outline" 
                onClick={() => navigate('/signup')}
                className="w-full h-12 border-2 border-gray-100 hover:bg-gray-50 text-gray-600 font-bold rounded-xl"
              >
                회원가입
              </Button>
            </>
          )}
          
          <div className="text-center mt-4">
             <button 
               onClick={() => navigate('/find-account')}
               className="text-sm text-gray-400 hover:text-[#9D8AD6] font-medium underline underline-offset-4"
             >
               아이디/비밀번호 찾기
             </button>
          </div>
        </div>

      </div>
    </div>
  );
}