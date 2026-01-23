import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Swal from 'sweetalert2';
import { ArrowLeft, ChevronLeft, Lock } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';

export default function FindAccountPage() {
  const navigate = useNavigate();
  
  const [activeTab, setActiveTab] = useState<'findId' | 'resetPw'>('findId');
  
  // 단계: 'select'(수단선택) -> 'input'(정보입력) -> 'reset'(비밀번호재설정)
  const [step, setStep] = useState<'select' | 'input' | 'reset'>('select');
  const [method, setMethod] = useState<'email' | 'phone' | null>(null);

  const [formData, setFormData] = useState({
    name: '',
    userId: '',
    email: '',
    phone: '',
    newPassword: '',
    confirmNewPassword: ''
  });

  // 초기화
  const handleTabChange = (tab: 'findId' | 'resetPw') => {
    setActiveTab(tab);
    setStep('select');
    setMethod(null);
    setFormData({ name: '', userId: '', email: '', phone: '', newPassword: '', confirmNewPassword: '' });
  };

  // 1단계 -> 2단계 이동
  const handleMethodSelect = (selectedMethod: 'email' | 'phone') => {
    setMethod(selectedMethod);
    setStep('input');
  };

  // 2단계 완료 (본인확인)
  const handleVerify = () => {
    // 유효성 검사 (입력 확인)
    if (!formData.name || (method === 'email' && !formData.email) || (method === 'phone' && !formData.phone)) {
      Swal.fire({ icon: 'error', title: '입력 오류', text: '정보를 모두 입력해주세요.', confirmButtonColor: '#9D8AD6' });
      return;
    }

    if (activeTab === 'findId') {
      // [아이디 찾기]는 여기서 끝 (결과 보여줌)
      Swal.fire({
        icon: 'success',
        title: '아이디 찾기 성공',
        html: `회원님의 아이디는<br/><strong style="font-size: 1.2em; color: #9D8AD6;">[ user1234 ]</strong> 입니다.`,
        confirmButtonColor: '#9D8AD6'
      }).then(() => navigate('/login'));
    } else {
      // [비밀번호 재설정]은 다음 단계로 이동 (새 비번 입력)
      Swal.fire({
        icon: 'success',
        title: '인증 성공',
        text: '새로운 비밀번호를 설정해주세요.',
        confirmButtonColor: '#9D8AD6',
        timer: 1500,
        showConfirmButton: false
      });
      setStep('reset'); // 3단계로 이동
    }
  };

  // 3단계 완료 (비밀번호 변경)
  const handlePasswordReset = async () => {
    if (formData.newPassword.length < 8) {
      await Swal.fire({ icon: 'warning', text: '비밀번호는 8자 이상이어야 합니다.', confirmButtonColor: '#9D8AD6' });
      return;
    }
    if (formData.newPassword !== formData.confirmNewPassword) {
      await Swal.fire({ icon: 'error', text: '비밀번호가 서로 일치하지 않습니다.', confirmButtonColor: '#9D8AD6' });
      return;
    }

    // 성공 처리
    await Swal.fire({
      icon: 'success',
      title: '비밀번호 변경 완료',
      text: '새로운 비밀번호로 로그인해주세요.',
      confirmButtonColor: '#9D8AD6'
    });
    navigate('/login');
  };

  return (
    <div className="min-h-screen w-full flex flex-col items-center justify-center bg-gradient-to-br from-[#f9f8fc] via-[#E6E6FA] to-[#d1c7ee] p-4">
      
      {/* 헤더 */}
      <div className="w-full max-w-[520px] mb-6">
        <button onClick={() => navigate('/login')} className="flex items-center gap-2 text-gray-500 hover:text-gray-900 transition-colors">
          <ArrowLeft className="w-5 h-5" />
          <span className="text-lg font-bold font-['Arial']">뒤로 가기</span>
        </button>
      </div>

      {/* 메인 카드 */}
      <div className="w-full max-w-[520px] bg-white rounded-[32px] shadow-xl overflow-hidden min-h-[550px] flex flex-col">
        
        {/* 상단 탭 */}
        <div className="flex w-full border-b border-gray-100">
          <button onClick={() => handleTabChange('findId')} className={`flex-1 py-6 text-xl font-bold transition-all ${activeTab === 'findId' ? 'bg-white text-[#9D8AD6] border-b-4 border-[#9D8AD6]' : 'bg-gray-50 text-gray-400 hover:bg-gray-100'}`}>
            아이디 찾기
          </button>
          <button onClick={() => handleTabChange('resetPw')} className={`flex-1 py-6 text-xl font-bold transition-all ${activeTab === 'resetPw' ? 'bg-white text-[#9D8AD6] border-b-4 border-[#9D8AD6]' : 'bg-gray-50 text-gray-400 hover:bg-gray-100'}`}>
            비밀번호 재설정
          </button>
        </div>

        <div className="p-10 flex-1 flex flex-col justify-center animate-fade-in">
          
          {/* [1단계] 인증 수단 선택 */}
          {step === 'select' && (
            <div className="flex flex-col items-center w-full">
              <h2 className="text-3xl font-bold text-gray-900 mb-6 font-['Arial']">
                {activeTab === 'findId' ? '아이디 찾기' : '비밀번호 재설정'}
              </h2>
              <div className="w-full h-[1px] bg-gray-200 mb-10"></div>
              <div className="w-full space-y-4">
                <button onClick={() => handleMethodSelect('email')} className="w-full h-16 bg-[#9D8AD6] hover:bg-[#8b7ad6] text-white text-lg font-bold rounded-xl shadow-md transition-all">
                  회원정보에 등록된 이메일
                </button>
                <button onClick={() => handleMethodSelect('phone')} className="w-full h-16 bg-[#9D8AD6] hover:bg-[#8b7ad6] text-white text-lg font-bold rounded-xl shadow-md transition-all">
                  회원정보에 등록된 휴대전화번호
                </button>
              </div>
            </div>
          )}

          {/* [2단계] 본인 확인 정보 입력 */}
          {step === 'input' && (
            <div className="flex flex-col w-full h-full">
              <div className="flex items-center mb-8 relative">
                <button onClick={() => setStep('select')} className="absolute left-0 p-2 hover:bg-gray-100 rounded-full">
                  <ChevronLeft className="w-6 h-6 text-gray-500" />
                </button>
                <h2 className="w-full text-center text-2xl font-bold text-gray-900">본인 확인</h2>
              </div>

              <div className="space-y-6 flex-1">
                {activeTab === 'resetPw' && (
                  <div className="space-y-2">
                    <Label className="text-base font-bold text-gray-700">아이디</Label>
                    <Input value={formData.userId} onChange={(e) => setFormData({...formData, userId: e.target.value})} placeholder="아이디 입력" className="h-14 bg-gray-50 border-gray-200 rounded-xl focus:border-[#9D8AD6] text-lg px-4" />
                  </div>
                )}
                <div className="space-y-2">
                  <Label className="text-base font-bold text-gray-700">이름</Label>
                  <Input value={formData.name} onChange={(e) => setFormData({...formData, name: e.target.value})} placeholder="이름 입력" className="h-14 bg-gray-50 border-gray-200 rounded-xl focus:border-[#9D8AD6] text-lg px-4" />
                </div>
                {method === 'email' ? (
                  <div className="space-y-2">
                    <Label className="text-base font-bold text-gray-700">이메일</Label>
                    <Input type="email" value={formData.email} onChange={(e) => setFormData({...formData, email: e.target.value})} placeholder="example@email.com" className="h-14 bg-gray-50 border-gray-200 rounded-xl focus:border-[#9D8AD6] text-lg px-4" />
                  </div>
                ) : (
                  <div className="space-y-2">
                    <Label className="text-base font-bold text-gray-700">휴대전화번호</Label>
                    <div className="flex gap-2">
                      <Input type="tel" value={formData.phone} onChange={(e) => setFormData({...formData, phone: e.target.value})} placeholder="010-0000-0000" className="h-14 bg-gray-50 border-gray-200 rounded-xl focus:border-[#9D8AD6] text-lg px-4" />
                      <Button className="h-14 w-24 bg-gray-200 text-gray-600 hover:bg-gray-300 rounded-xl font-bold">인증</Button>
                    </div>
                  </div>
                )}
              </div>
              <Button onClick={handleVerify} className="w-full h-16 bg-[#9D8AD6] hover:bg-[#8b7ad6] text-white text-xl font-bold rounded-xl shadow-lg shadow-[#9D8AD6]/30 mt-8">
                {activeTab === 'findId' ? '아이디 찾기' : '다음 단계'}
              </Button>
            </div>
          )}

          {/* [3단계] 새 비밀번호 입력 (비밀번호 재설정 탭 전용) */}
          {step === 'reset' && (
            <div className="flex flex-col w-full h-full animate-fade-in">
              <div className="flex items-center mb-8 relative">
                <button onClick={() => setStep('input')} className="absolute left-0 p-2 hover:bg-gray-100 rounded-full">
                  <ChevronLeft className="w-6 h-6 text-gray-500" />
                </button>
                <h2 className="w-full text-center text-2xl font-bold text-gray-900">새 비밀번호 설정</h2>
              </div>

              <div className="space-y-6 flex-1">
                <div className="space-y-2">
                  <Label className="text-base font-bold text-gray-700">새 비밀번호</Label>
                  <div className="relative">
                    <Lock className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                    <Input type="password" value={formData.newPassword} onChange={(e) => setFormData({...formData, newPassword: e.target.value})} placeholder="8자 이상 입력" className="h-14 pl-12 bg-gray-50 border-gray-200 rounded-xl focus:border-[#9D8AD6] text-lg" />
                  </div>
                </div>
                <div className="space-y-2">
                  <Label className="text-base font-bold text-gray-700">새 비밀번호 확인</Label>
                  <div className="relative">
                    <Lock className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                    <Input type="password" value={formData.confirmNewPassword} onChange={(e) => setFormData({...formData, confirmNewPassword: e.target.value})} placeholder="비밀번호 재입력" className="h-14 pl-12 bg-gray-50 border-gray-200 rounded-xl focus:border-[#9D8AD6] text-lg" />
                  </div>
                </div>
              </div>
              <Button onClick={handlePasswordReset} className="w-full h-16 bg-[#9D8AD6] hover:bg-[#8b7ad6] text-white text-xl font-bold rounded-xl shadow-lg shadow-[#9D8AD6]/30 mt-8">
                비밀번호 변경 완료
              </Button>
            </div>
          )}

        </div>
      </div>
    </div>
  );
}