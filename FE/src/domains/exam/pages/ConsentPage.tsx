import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ShieldCheck, Database, Hospital, AlertTriangle } from 'lucide-react';
import { Button } from '@/components/common/Button';
import ConsentHeader from '../components/ConsentHeader';
import ConsentItem from '../components/ConsentItem';
import ConsentNotice from '../components/ConsentNotice';
import { startExam } from '../api/examApi';
import Swal from 'sweetalert2';

const ConsentPage = () => {
  const navigate = useNavigate();
  const [isLoading, setIsLoading] = useState(false);
  const [agreements, setAgreements] = useState({
    media: false,     // 1. 영상·음성 수집
    aiUsage: false,   // 2. AI 학습 미사용 고지
    hospital: false,  // 3. 제3자 제공 (병원)
    disclaimer: false // 4. 한계 및 면책
  });

  const allRequiredAgreed = Object.values(agreements).every(Boolean);

  const handleToggle = (key: keyof typeof agreements) => {
    setAgreements((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  const handleStartExam = async () => {
    if (!allRequiredAgreed) return;

    setIsLoading(true);
    try {
      // ✅ 1. childId 가져오기
      const childId = localStorage.getItem('selectedChildId');
      if (!childId) {
        Swal.fire({
          title: '자녀 정보 없음',
          text: '자녀 정보를 찾을 수 없습니다. 홈 화면으로 돌아갑니다.',
          icon: 'error'
        });
        navigate('/parent/dashboard');
        return;
      }

      // ✅ 2. 검사 시작 API 호출 - examId 받기
      const examId = await startExam(childId);

      // ✅ 3. examId를 localStorage에 저장
      localStorage.setItem('examId', examId);
      localStorage.setItem('currentExamId', examId);
      console.log(`✅ examId 저장 완료: ${examId}`);

      // ✅ 4. 가이드 페이지로 이동
      navigate('/exam/guide');
    } catch (error: any) {
      console.error('❌ 검사 시작 에러:', error);
      const errorMessage = error?.response?.data?.message || error.message || '검사를 시작할 수 없습니다.';
      Swal.fire({
        title: '검사 시작 실패',
        text: errorMessage,
        icon: 'error'
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex flex-col items-center w-full">
      <ConsentHeader
        currentStep={1}
        totalSteps={3}
        onBack={() => navigate('/parent/dashboard')}
      />

      <main className="w-full max-w-[1187px] mt-10 mb-20">
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-gray-800 mb-3">검사 시작 전 동의</h1>
          <p className="text-xl text-gray-600">안전하고 정밀한 분석을 위해 아래 필수 동의를 진행해주세요.</p>
        </div>

        <div className="bg-white rounded-3xl shadow-xl p-10 flex flex-col gap-8">
          {/* 1. 영상·음성 정보 수집 및 이용 동의 */}
          <ConsentItem
            icon={<ShieldCheck />}
            title="1. 영상·음성 정보 수집 및 이용 동의 (필수)"
            isChecked={agreements.media}
            onToggle={() => handleToggle('media')}
          >
            <ul className="text-sm text-gray-600 space-y-1 mt-2">
              <li>• <strong>수집 항목</strong>: 보호자 및 아동의 얼굴 영상, 음성, 행동 정보(호명 반응, 눈맞춤 등), 시선 및 표정 변화</li>
              <li>• <strong>이용 목적</strong>: AI 알고리즘을 통한 행동 정량 분석, 자폐 스펙트럼 진단 보조 데이터 산출 및 리포트 생성</li>
              <li>• <strong>보유 기간</strong>: 리포트 생성 이후 <strong>5년간 보관</strong>되며, 기간 경과 후 지체 없이 파기됩니다.</li>
            </ul>
          </ConsentItem>

          {/* 2. AI 모델 학습 미사용 고지 */}
          <ConsentItem
            icon={<Database />}
            title="2. AI 모델 학습 및 고도화 목적 사용에 대한 고지 (필수)"
            isChecked={agreements.aiUsage}
            onToggle={() => handleToggle('aiUsage')}
          >
            <p className="text-sm text-gray-600">
              수집된 영상 및 음성 데이터는 <strong>AI 모델 학습, 성능 개선, 고도화, 재학습 목적에 사용되지 않습니다.</strong>
              오직 검사 결과 산출 및 사후 분쟁 대응, 서비스 품질 검증 목적에 한하여 보관합니다.
            </p>
          </ConsentItem>

          {/* 3. 개인정보 제3자 제공 동의 */}
          <ConsentItem
            icon={<Hospital />}
            title="3. 개인정보의 제3자 제공 동의 (필수 – 병원 제공)"
            isChecked={agreements.hospital}
            onToggle={() => handleToggle('hospital')}
          >
            <ul className="text-sm text-gray-600 space-y-1 mt-2">
              <li>• <strong>제공 대상</strong>: 초대코드를 발급한 제휴 의료기관</li>
              <li>• <strong>제공 항목</strong>: AI 분석 결과 리포트 (※ <strong>원본 영상 및 음성 데이터 제외</strong>)</li>
              <li>• <strong>보유 기간</strong>: 해당 의료기관의 관련 법령상 의무기록 보존 기간</li>
            </ul>
          </ConsentItem>

          {/* 4. AI 분석의 한계 및 면책 동의 */}
          <ConsentItem
            icon={<AlertTriangle />}
            title="4. AI 분석의 한계 및 면책 동의 (필수)"
            isChecked={agreements.disclaimer}
            onToggle={() => handleToggle('disclaimer')}
          >
            <p className="text-sm text-gray-600">
              본 결과는 촬영 환경, 아동의 상태 등에 따라 차이가 발생할 수 있으며, <strong>의학적 확진이나 치료 판단의 근거로 단독 사용될 수 없습니다.</strong>
            </p>
          </ConsentItem>

          <ConsentNotice />
        </div>

        <Button
          disabled={!allRequiredAgreed || isLoading}
          variant={allRequiredAgreed ? "default" : "secondary"}
          size="lg"
          className="w-full h-16 mt-10 text-xl"
          onClick={handleStartExam}
        >
          {isLoading ? "검사 시작 중..." : allRequiredAgreed ? "약관 동의 및 검사 시작" : "모든 필수 항목에 동의해주세요"}
        </Button>
      </main>
    </div>
  );
};

export default ConsentPage;