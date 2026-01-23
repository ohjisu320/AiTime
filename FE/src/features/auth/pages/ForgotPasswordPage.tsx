import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Swal from 'sweetalert2';
import { ArrowLeft, Mail } from 'lucide-react';

export default function ForgotPasswordPage() {
  const navigate = useNavigate();
  const [email, setEmail] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!email) {
      await Swal.fire({
        icon: 'error',
        title: '이메일을 입력해주세요',
        confirmButtonColor: '#9d8ad6'
      });
      return;
    }

    // 비밀번호 재설정 시뮬레이션
    await Swal.fire({
      icon: 'success',
      title: '비밀번호 재설정 이메일 발송',
      html: `<p>${email}로<br/>비밀번호 재설정 링크를 발송했습니다.</p><p class="text-sm text-gray-500 mt-2">이메일을 확인해주세요.</p>`,
      confirmButtonColor: '#9d8ad6'
    });

    navigate('/login'); // 로그인 페이지로 돌아가기
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#f9f8fc] via-[#E6E6FA] to-[#d1c7ee] flex items-center justify-center p-6">
      <div className="w-full max-w-md fade-in">
        {/* 뒤로 가기 버튼 */}
        <button
          onClick={() => navigate('/login')}
          className="flex items-center gap-2 text-gray-700 hover:text-gray-900 mb-6 transition-colors"
        >
          <ArrowLeft className="w-5 h-5" />
          <span>로그인으로 돌아가기</span>
        </button>

        {/* 메인 카드 */}
        <div className="aitime-card">
          <h2 className="text-2xl font-bold text-gray-800 mb-2">
            비밀번호 재설정
          </h2>
          <p className="text-gray-600 mb-6">
            가입하신 이메일 주소를 입력해주세요.
            <br />
            비밀번호 재설정 링크를 보내드립니다.
          </p>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">
                이메일
              </label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="example@email.com"
                  className="aitime-input pl-11"
                  required
                />
              </div>
            </div>

            <button
              type="submit"
              className="w-full py-4 bg-[#9d8ad6] hover:bg-[#8670c8] text-white rounded-xl font-semibold transition-all"
            >
              재설정 링크 발송
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}