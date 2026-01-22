import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Swal from 'sweetalert2';
import { ArrowLeft } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Checkbox } from '@/components/ui/checkbox'; // ✅ 체크박스 추가

export default function SignupPage() {
  const navigate = useNavigate();
  
  // 현재 단계: 1(약관동의) -> 2(정보입력)
  const [step, setStep] = useState<1 | 2>(1);
  
  // 약관 동의 상태
  const [agreed, setAgreed] = useState(false);

  // 입력값 상태
  const [formData, setFormData] = useState({
    id: '',
    password: '',
    confirmPassword: '',
    name: '',
    phone: '',
    email: '',
  });

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  // 1단계 -> 2단계 이동 핸들러
  const handleNextStep = () => {
    if (!agreed) {
      Swal.fire({ 
        icon: 'warning', 
        text: '약관에 동의해주세요.', 
        confirmButtonColor: '#9D8AD6' 
      });
      return;
    }
    setStep(2);
  };

  // 최종 가입 핸들러
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (formData.password !== formData.confirmPassword) {
      await Swal.fire({ icon: 'error', text: '비밀번호가 서로 다릅니다.', confirmButtonColor: '#9D8AD6' });
      return;
    }

    await Swal.fire({
      icon: 'success',
      title: '환영합니다!',
      text: '회원가입이 완료되었습니다.',
      confirmButtonColor: '#9D8AD6'
    });
    
    navigate('/login');
  };

  return (
    <div className="min-h-screen w-full flex flex-col items-center justify-start bg-gradient-to-br from-[#f9f8fc] via-[#E6E6FA] to-[#d1c7ee] p-6 overflow-y-auto">
      
      {/* 1. 상단 헤더 */}
      <div className="w-full max-w-[800px] flex items-center justify-start gap-6 mb-8 mt-4">
        <div className="flex items-center gap-2">
           <div className="w-10 h-10 bg-gradient-to-b from-[#9D8AD6] to-violet-500 rounded-xl flex items-center justify-center text-white font-bold">Ai</div>
           <span className="text-3xl font-bold text-gray-800 font-['Arial']">AiTime</span>
        </div>
        <div className="h-6 w-[1px] bg-gray-300"></div>
        <button 
          onClick={() => {
            if (step === 2) setStep(1); // 2단계면 1단계로
            else navigate('/login');    // 1단계면 로그인으로
          }}
          className="flex items-center gap-2 text-gray-500 hover:text-gray-900 transition-colors"
        >
          <ArrowLeft className="w-5 h-5" />
          <span className="text-lg font-bold font-['Arial']">
            {step === 1 ? '로그인으로' : '이전 단계'}
          </span>
        </button>
      </div>

      {/* 2. 단계 표시 (Stepper) */}
      <div className="w-full max-w-[400px] mb-8 flex items-center justify-between px-4">
        {/* 1단계 */}
        <div className="flex flex-col items-center gap-2 relative z-10">
          <div className={`w-10 h-10 rounded-full flex items-center justify-center font-bold shadow-md transition-colors ${step >= 1 ? 'bg-[#9D8AD6] text-white' : 'bg-gray-200 text-gray-500'}`}>
            1
          </div>
          <span className={`text-sm font-bold whitespace-nowrap transition-colors ${step >= 1 ? 'text-[#9D8AD6]' : 'text-gray-400'}`}>
            약관 동의
          </span>
        </div>

        {/* 연결선 */}
        <div className="flex-1 h-[3px] bg-gray-200 mx-4 rounded-full relative overflow-hidden">
          <div className={`absolute top-0 left-0 h-full bg-[#9D8AD6] transition-all duration-300 ${step === 2 ? 'w-full' : 'w-0'}`}></div>
        </div>

        {/* 2단계 */}
        <div className="flex flex-col items-center gap-2 relative z-10">
            <div className={`w-10 h-10 rounded-full flex items-center justify-center font-bold shadow-md transition-colors ${step === 2 ? 'bg-[#9D8AD6] text-white ring-4 ring-[#9D8AD6]/20' : 'bg-gray-200 text-gray-500'}`}>
              2
            </div>
            <span className={`text-sm font-bold whitespace-nowrap transition-colors ${step === 2 ? 'text-gray-800' : 'text-gray-400'}`}>
              회원정보 입력
            </span>
        </div>
      </div>

      {/* ======================================================== */}
      {/* 3-A. [1단계] 약관 동의 페이지 (내용 없음) */}
      {/* ======================================================== */}
      {step === 1 && (
        <div className="w-full max-w-[800px] bg-white rounded-[32px] shadow-xl p-8 md:p-12 animate-fade-in">
          <h2 className="text-2xl font-bold text-gray-800 mb-6">서비스 이용약관</h2>
          
          {/* 빈 약관 박스 */}
          <div className="w-full h-[400px] bg-gray-50 rounded-xl border border-gray-200 p-6 mb-8 overflow-y-auto text-gray-400 flex items-center justify-center">
            (약관 내용이 들어갈 자리입니다)
          </div>

          {/* 동의 체크박스 */}
          <div className="flex items-center space-x-3 mb-8 p-4 bg-gray-50 rounded-xl cursor-pointer hover:bg-gray-100 transition-colors" onClick={() => setAgreed(!agreed)}>
            <Checkbox 
              id="terms" 
              checked={agreed}
              onCheckedChange={(checked) => setAgreed(checked as boolean)}
              className="w-6 h-6 border-2 data-[state=checked]:bg-[#9D8AD6] data-[state=checked]:border-[#9D8AD6]"
            />
            <Label htmlFor="terms" className="text-lg text-gray-700 font-bold cursor-pointer">
              위 약관을 확인하였으며, 이에 동의합니다.
            </Label>
          </div>

          <Button 
            onClick={handleNextStep}
            className={`w-full h-16 text-xl font-bold rounded-2xl shadow-lg mt-2 transition-all ${
              agreed 
              ? 'bg-[#9D8AD6] hover:bg-[#8b7ad6] text-white shadow-[#9D8AD6]/30' 
              : 'bg-gray-300 text-gray-500 cursor-not-allowed'
            }`}
          >
            다음으로 넘어가기
          </Button>
        </div>
      )}


      {/* ======================================================== */}
      {/* 3-B. [2단계] 회원정보 입력 페이지 (기존 코드) */}
      {/* ======================================================== */}
      {step === 2 && (
        <div className="w-full max-w-[800px] bg-white rounded-[32px] shadow-xl p-8 md:p-12 animate-fade-in">
          <h2 className="text-2xl font-bold text-gray-800 mb-8 border-b pb-4">회원정보 입력</h2>

          <form onSubmit={handleSubmit} className="space-y-8">
            <div className="space-y-2">
              <Label className="text-lg font-bold text-gray-700">아이디</Label>
              <div className="flex gap-3">
                <Input name="id" value={formData.id} onChange={handleChange} placeholder="아이디를 입력하세요" className="h-14 bg-white border-2 border-gray-200 rounded-xl text-lg px-4 focus:border-[#9D8AD6]" />
                <Button type="button" className="h-14 w-32 bg-slate-200 hover:bg-slate-300 text-slate-600 font-bold rounded-xl text-lg">중복확인</Button>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="space-y-2">
                <Label className="text-lg font-bold text-gray-700">비밀번호</Label>
                <Input type="password" name="password" value={formData.password} onChange={handleChange} placeholder="8자 이상 입력" className="h-14 bg-white border-2 border-gray-200 rounded-xl text-lg px-4 focus:border-[#9D8AD6]" />
              </div>
              <div className="space-y-2">
                <Label className="text-lg font-bold text-gray-700">비밀번호 확인</Label>
                <Input type="password" name="confirmPassword" value={formData.confirmPassword} onChange={handleChange} placeholder="비밀번호 재입력" className="h-14 bg-white border-2 border-gray-200 rounded-xl text-lg px-4 focus:border-[#9D8AD6]" />
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="space-y-2">
                <Label className="text-lg font-bold text-gray-700">보호자 이름</Label>
                <Input name="name" value={formData.name} onChange={handleChange} placeholder="이름 입력" className="h-14 bg-white border-2 border-gray-200 rounded-xl text-lg px-4 focus:border-[#9D8AD6]" />
              </div>
              <div className="space-y-2">
                <Label className="text-lg font-bold text-gray-700">이메일</Label>
                <Input type="email" name="email" value={formData.email} onChange={handleChange} placeholder="example@email.com" className="h-14 bg-white border-2 border-gray-200 rounded-xl text-lg px-4 focus:border-[#9D8AD6]" />
              </div>
            </div>

            <div className="space-y-2">
              <div className="flex justify-between items-end">
                <Label className="text-lg font-bold text-gray-700">휴대전화번호</Label>
                <span className="text-xs text-gray-400 font-medium mb-1 hidden md:block">* 등록된 번호로 아이디/비밀번호를 찾을 수 있습니다.</span>
              </div>
              <div className="flex gap-3">
                <Input type="tel" name="phone" value={formData.phone} onChange={handleChange} placeholder="010-1234-5678" className="h-14 bg-white border-2 border-gray-200 rounded-xl text-lg px-4 focus:border-[#9D8AD6]" />
                <Button type="button" className="h-14 w-32 bg-slate-200 hover:bg-slate-300 text-slate-600 font-bold rounded-xl text-lg">인증하기</Button>
              </div>
            </div>

            <Button type="submit" className="w-full h-16 bg-[#9D8AD6] hover:bg-[#8b7ad6] text-white text-xl font-bold rounded-2xl shadow-lg shadow-[#9D8AD6]/30 mt-8">
              회원가입 완료
            </Button>
          </form>
        </div>
      )}
      
      <div className="h-10"></div>
    </div>
  );
}