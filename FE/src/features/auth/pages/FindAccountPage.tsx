// src/features/auth/pages/FindAccountPage.tsx
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Swal from 'sweetalert2';
import { ArrowLeft, CheckCircle2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { cn } from '@/lib/utils';

// 화면 모드 타입 정의
type ViewMode = 'MENU' | 'FIND_ID' | 'RESET_PW';

export default function FindAccountPage() {
  const navigate = useNavigate();
  
  // 현재 화면 모드 상태
  const [mode, setMode] = useState<ViewMode>('MENU');

  // --- 공통 상태 ---
  const [phone, setPhone] = useState('');
  const [authCode, setAuthCode] = useState('');
  const [isPhoneVerified, setIsPhoneVerified] = useState(false); // 인증 완료 여부

  // --- 아이디 찾기 결과 상태 ---
  const [foundId, setFoundId] = useState<string | null>(null);

  // --- 비밀번호 재설정 상태 ---
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');

  // ------------------------------------------
  // 핸들러 함수들 (Mock Logic)
  // ------------------------------------------

  // 뒤로가기 핸들러
  const handleBack = () => {
    if (mode === 'MENU') {
      navigate('/login');
    } else {
      // 초기화 후 메뉴로 이동
      setMode('MENU');
      resetForm();
    }
  };

  // 폼 초기화
  const resetForm = () => {
    setPhone('');
    setAuthCode('');
    setIsPhoneVerified(false);
    setFoundId(null);
    setNewPassword('');
    setConfirmPassword('');
  };

  // 인증번호 요청 (Mock)
  const handleRequestAuth = () => {
    if (!phone) {
      Swal.fire({ icon: 'warning', text: '휴대전화번호를 입력해주세요.', confirmButtonColor: '#9593D9' });
      return;
    }
    Swal.fire({ icon: 'success', text: '인증번호가 발송되었습니다. (테스트: 1234)', confirmButtonColor: '#9593D9' });
  };

  // 인증번호 확인 (Mock)
  const handleVerifyAuth = () => {
    if (authCode === '1234') {
      setIsPhoneVerified(true);
      Swal.fire({ 
        icon: 'success', 
        title: '인증 성공',
        text: '휴대폰 인증이 완료되었습니다.', 
        confirmButtonColor: '#9593D9',
        timer: 1500,
        showConfirmButton: false
      });
    } else {
      Swal.fire({ icon: 'error', text: '인증번호가 일치하지 않습니다.', confirmButtonColor: '#9593D9' });
    }
  };

  // 아이디 찾기 실행 (Mock)
  const handleFindId = () => {
    // API 호출 시뮬레이션
    setTimeout(() => {
      setFoundId('aitime_parent'); // 찾은 아이디 예시
    }, 500);
  };

  // 비밀번호 재설정 실행 (Mock)
  const handleResetPassword = () => {
    if (newPassword !== confirmPassword) {
      Swal.fire({ icon: 'error', text: '비밀번호가 일치하지 않습니다.', confirmButtonColor: '#9593D9' });
      return;
    }
    Swal.fire({ 
      icon: 'success', 
      title: '변경 완료',
      text: '비밀번호가 성공적으로 변경되었습니다.', 
      confirmButtonColor: '#9593D9' 
    }).then(() => {
      navigate('/login');
    });
  };

  // ------------------------------------------
  // UI 컴포넌트
  // ------------------------------------------

  return (
    // ✨ justify-center 추가로 화면 정중앙 배치
    <div className="min-h-screen w-full flex flex-col items-center justify-center bg-[#E3E0F5] relative p-6 overflow-y-auto">
      
      {/* 헤더 영역 (카드 바로 위에 위치하도록 배치) */}
      <div className="w-full max-w-[1024px] h-20 relative flex items-center justify-center mb-6">
        {/* 뒤로가기 버튼 (좌측 상단) */}
        <button 
          onClick={handleBack}
          className="absolute left-0 top-1/2 -translate-y-1/2 flex items-center gap-3 text-gray-500 hover:text-[#9593D9] transition-colors"
        >
          <ArrowLeft className="w-6 h-6" /> {/* 아이콘 크기 확대 */}
          <span className="text-lg font-medium text-[#555555]"> {/* 폰트 크기 확대 */}
            뒤로 가기
          </span>
        </button>

        {/* 로고 (중앙) */}
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 bg-[#D9D9D9] rounded-2xl flex items-center justify-center shadow-sm" />
          <h1 className="text-5xl font-bold text-black font-['DM_Sans'] tracking-tight">
            AiTime
          </h1>
        </div>
      </div>

      {/* 메인 카드 컨테이너 */}
      {/* ✨ max-w-[1024px]로 너비 확대, min-h-[600px]로 높이 확보 */}
      <div className="w-full max-w-[1024px] bg-white rounded-[50px] shadow-[0_10px_40px_rgba(0,0,0,0.05)] p-12 md:p-20 mb-10 min-h-[600px] flex flex-col justify-center animate-fade-in">
        
        {/* ======================================================= */}
        {/* CASE 1: 메뉴 선택 (초기 화면) */}
        {/* ======================================================= */}
        {mode === 'MENU' && (
          <div className="flex flex-col gap-12">
            <h2 className="text-3xl font-bold text-center text-[#1A1A1A]">아이디 / 비밀번호 찾기</h2>
            
            <div className="flex flex-col md:flex-row gap-8">
              {/* 아이디 찾기 버튼 */}
              <button 
                onClick={() => setMode('FIND_ID')}
                // ✨ 높이 320px로 확대
                className="flex-1 h-[320px] bg-[#F3F0FF] hover:bg-[#EBE6FF] rounded-[40px] flex flex-col items-center justify-center gap-6 transition-all hover:scale-[1.02] group shadow-sm hover:shadow-md"
              >
                {/* 아이콘 원 확대 */}
                <div className="w-24 h-24 bg-white rounded-full flex items-center justify-center shadow-sm text-3xl font-bold text-[#9593D9] group-hover:text-[#7a78b8]">
                  ID
                </div>
                <div className="text-center">
                  <h3 className="text-2xl font-bold text-[#333]">아이디 찾기</h3>
                  <p className="text-base text-gray-500 mt-3 leading-relaxed">가입 시 등록한 휴대폰 번호로<br/>아이디를 조회합니다.</p>
                </div>
              </button>

              {/* 비밀번호 재설정 버튼 */}
              <button 
                onClick={() => setMode('RESET_PW')}
                className="flex-1 h-[320px] bg-[#F3F0FF] hover:bg-[#EBE6FF] rounded-[40px] flex flex-col items-center justify-center gap-6 transition-all hover:scale-[1.02] group shadow-sm hover:shadow-md"
              >
                 <div className="w-24 h-24 bg-white rounded-full flex items-center justify-center shadow-sm text-3xl font-bold text-[#9593D9] group-hover:text-[#7a78b8]">
                  PW
                </div>
                <div className="text-center">
                  <h3 className="text-2xl font-bold text-[#333]">비밀번호 재설정</h3>
                  <p className="text-base text-gray-500 mt-3 leading-relaxed">본인 인증을 완료한 후 새로운<br/>비밀번호로 변경합니다.</p>
                </div>
              </button>
            </div>
          </div>
        )}

        {/* ======================================================= */}
        {/* CASE 2: 아이디 찾기 */}
        {/* ======================================================= */}
        {mode === 'FIND_ID' && !foundId && (
          <div className="w-full max-w-[600px] mx-auto">
            <h2 className="text-3xl font-bold text-center text-[#1A1A1A] mb-12">아이디 찾기</h2>
            
            <div className="space-y-8">
              <div className="space-y-3">
                <Label className="text-lg font-bold text-[#333]">휴대전화번호</Label>
                <div className="flex gap-3">
                  <Input 
                    value={phone}
                    onChange={(e) => setPhone(e.target.value)}
                    placeholder="010-1234-5678" 
                    className="flex-1 h-14 bg-gray-50 border-gray-200 rounded-2xl text-lg px-5"
                    disabled={isPhoneVerified}
                  />
                  <Button 
                    onClick={handleRequestAuth}
                    disabled={isPhoneVerified}
                    className="h-14 w-[120px] bg-[#D6D3F0] hover:bg-[#c2bde6] text-[#5A5880] text-lg font-bold rounded-2xl shadow-none"
                  >
                    인증하기
                  </Button>
                </div>
              </div>

              {/* 인증번호 입력창 */}
              <div className="space-y-3">
                <div className="flex gap-3">
                  <Input 
                    value={authCode}
                    onChange={(e) => setAuthCode(e.target.value)}
                    placeholder="인증번호 입력" 
                    className="flex-1 h-14 bg-gray-50 border-gray-200 rounded-2xl text-lg px-5"
                    disabled={isPhoneVerified}
                  />
                  <Button 
                    onClick={handleVerifyAuth}
                    disabled={isPhoneVerified}
                    className="h-14 w-[120px] bg-[#9593D9] hover:bg-[#8381c9] text-white text-lg font-bold rounded-2xl shadow-none"
                  >
                    확인
                  </Button>
                </div>
              </div>

              {/* 확인 버튼 */}
              <Button 
                onClick={handleFindId}
                disabled={!isPhoneVerified}
                className={cn(
                  "w-full h-16 text-xl font-bold rounded-2xl mt-10 transition-all",
                  isPhoneVerified 
                    ? "bg-[#9593D9] hover:bg-[#8381c9] text-white shadow-lg" 
                    : "bg-gray-300 text-gray-500 cursor-not-allowed"
                )}
              >
                아이디 찾기
              </Button>
            </div>
          </div>
        )}

        {/* ======================================================= */}
        {/* CASE 2-Result: 아이디 찾기 결과 */}
        {/* ======================================================= */}
        {mode === 'FIND_ID' && foundId && (
           <div className="w-full max-w-[600px] mx-auto text-center">
             <h2 className="text-3xl font-bold text-[#1A1A1A] mb-14">아이디 찾기</h2>
             
             <div className="py-10">
               <p className="text-gray-500 text-xl mb-6">귀하의 아이디는</p>
               <div className="bg-[#F3F0FF] py-8 rounded-[30px] border border-[#9593D9]/20 shadow-sm">
                 <span className="text-4xl font-bold text-[#9593D9] tracking-wide">
                   {foundId}
                 </span>
               </div>
               <p className="text-gray-500 text-xl mt-6">입니다.</p>
             </div>

             <div className="flex flex-col gap-4 mt-10">
               <Button 
                 onClick={() => navigate('/login')}
                 className="w-full h-16 bg-[#9593D9] hover:bg-[#8381c9] text-white text-xl font-bold rounded-2xl shadow-lg"
               >
                 로그인하기
               </Button>
               <Button 
                 onClick={() => {
                   resetForm();
                   setMode('RESET_PW');
                 }}
                 className="w-full h-16 bg-[#D6D3F0] hover:bg-[#c2bde6] text-[#5A5880] text-xl font-bold rounded-2xl shadow-none"
               >
                 비밀번호 재설정
               </Button>
             </div>
           </div>
        )}


        {/* ======================================================= */}
        {/* CASE 3: 비밀번호 재설정 */}
        {/* ======================================================= */}
        {mode === 'RESET_PW' && (
          <div className="w-full max-w-[600px] mx-auto">
            <h2 className="text-3xl font-bold text-center text-[#1A1A1A] mb-12">비밀번호 재설정</h2>
            
            <div className="space-y-8">
              
              {/* --- 1. 휴대폰 인증 섹션 --- */}
              <div className="space-y-6 pb-8 border-b border-gray-100">
                <div className="space-y-3">
                  <div className="flex justify-between items-end">
                    <Label className="text-lg font-bold text-[#333]">휴대전화번호</Label>
                    {isPhoneVerified && <span className="text-sm text-[#9593D9] font-bold flex items-center gap-1"><CheckCircle2 className="w-4 h-4"/>인증 완료</span>}
                  </div>
                  <div className="flex gap-3">
                    <Input 
                      value={phone}
                      onChange={(e) => setPhone(e.target.value)}
                      placeholder="010-1234-5678" 
                      className="flex-1 h-14 bg-gray-50 border-gray-200 rounded-2xl text-lg px-5"
                      disabled={isPhoneVerified}
                    />
                    <Button 
                      onClick={handleRequestAuth}
                      disabled={isPhoneVerified}
                      className="h-14 w-[120px] bg-[#D6D3F0] hover:bg-[#c2bde6] text-[#5A5880] text-lg font-bold rounded-2xl shadow-none"
                    >
                      인증요청
                    </Button>
                  </div>
                </div>

                <div className="flex gap-3">
                  <Input 
                    value={authCode}
                    onChange={(e) => setAuthCode(e.target.value)}
                    placeholder="인증번호 입력" 
                    className="flex-1 h-14 bg-gray-50 border-gray-200 rounded-2xl text-lg px-5"
                    disabled={isPhoneVerified}
                  />
                  <Button 
                    onClick={handleVerifyAuth}
                    disabled={isPhoneVerified}
                    className="h-14 w-[120px] bg-[#9593D9] hover:bg-[#8381c9] text-white text-lg font-bold rounded-2xl shadow-none"
                  >
                    확인
                  </Button>
                </div>
              </div>

              {/* --- 2. 새 비밀번호 입력 섹션 (인증 후 보임) --- */}
              {isPhoneVerified && (
                <div className="space-y-6 animate-fade-in pt-4">
                  <div className="space-y-3">
                    <Label className="text-lg font-bold text-[#333]">새로운 비밀번호</Label>
                    <Input 
                      type="password"
                      value={newPassword}
                      onChange={(e) => setNewPassword(e.target.value)}
                      placeholder="새 비밀번호 입력" 
                      className="h-14 bg-gray-50 border-gray-200 rounded-2xl text-lg px-5"
                    />
                  </div>
                  <div className="space-y-3">
                    <Label className="text-lg font-bold text-[#333]">비밀번호 확인</Label>
                    <Input 
                      type="password"
                      value={confirmPassword}
                      onChange={(e) => setConfirmPassword(e.target.value)}
                      placeholder="비밀번호 재입력" 
                      className="h-14 bg-gray-50 border-gray-200 rounded-2xl text-lg px-5"
                    />
                     {newPassword && confirmPassword && newPassword !== confirmPassword && (
                        <p className="text-sm text-red-500 pl-2">비밀번호가 일치하지 않습니다.</p>
                      )}
                  </div>

                   <Button 
                    onClick={handleResetPassword}
                    className="w-full h-16 bg-[#9593D9] hover:bg-[#8381c9] text-white text-xl font-bold rounded-2xl mt-8 shadow-lg"
                  >
                    확인
                  </Button>
                </div>
              )}
            </div>
          </div>
        )}

      </div>
    </div>
  );
}